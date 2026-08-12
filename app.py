# =============================================================================
# app.py — Flask Application Entry Point
# Fake News Detection REST API + Web Server
# =============================================================================

import os
import sys
import re
import json
import time
import uuid
import string
import logging
import datetime
import urllib.parse
import urllib.request

import joblib
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from flask import (
    Flask, render_template, request, jsonify,
    abort, send_from_directory
)
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask app setup
# ---------------------------------------------------------------------------
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR       = os.path.join(BASE_DIR, "model")
PREDICTIONS_DIR = os.path.join("/tmp", "saved_predictions")
HISTORY_FILE    = os.path.join(PREDICTIONS_DIR, "history.json")

os.makedirs(PREDICTIONS_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Stopwords (Static NLTK English stopwords list to prevent Vercel filesystem writes)
# ---------------------------------------------------------------------------
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "ain", "all", "am", "an",
    "and", "any", "are", "aren", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can", "couldn",
    "couldn't", "d", "did", "didn", "didn't", "do", "does", "doesn", "doesn't",
    "doing", "don", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "hadn", "hadn't", "has", "hasn", "hasn't", "have", "haven",
    "haven't", "having", "he", "he'd", "he'll", "her", "here", "hers", "herself",
    "he's", "him", "himself", "his", "how", "i", "i'd", "if", "i'll", "i'm", "in",
    "into", "is", "isn", "isn't", "it", "it'd", "it'll", "it's", "its", "itself",
    "i've", "just", "ll", "m", "ma", "me", "mightn", "mightn't", "more", "most",
    "mustn", "mustn't", "my", "myself", "needn", "needn't", "no", "nor", "not",
    "now", "o", "of", "off", "on", "once", "only", "or", "other", "our", "ours",
    "ourselves", "out", "over", "own", "re", "s", "same", "shan", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn", "shouldn't", "should've",
    "so", "some", "such", "t", "than", "that", "that'll", "the", "their", "theirs",
    "them", "themselves", "then", "there", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until",
    "up", "ve", "very", "was", "wasn", "wasn't", "we", "we'd", "we'll", "we're",
    "were", "weren", "weren't", "we've", "what", "when", "where", "which", "while",
    "who", "whom", "why", "will", "with", "won", "won't", "wouldn", "wouldn't",
    "y", "you", "you'd", "you'll", "your", "you're", "yours", "yourself", "yourselves",
    "you've"
}

# ---------------------------------------------------------------------------
# Load ML model & vectorizer
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
VECT_PATH  = os.path.join(MODEL_DIR, "vectorizer.pkl")
META_PATH  = os.path.join(MODEL_DIR, "metadata.pkl")

_model      = None
_vectorizer = None
_metadata   = {}

def load_model():
    """Load the trained model and vectorizer from disk."""
    global _model, _vectorizer, _metadata

    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECT_PATH):
        logger.warning(
            "Model files not found. Please run: python train_model.py"
        )
        return False

    try:
        _model      = joblib.load(MODEL_PATH)
        _vectorizer = joblib.load(VECT_PATH)
        if os.path.exists(META_PATH):
            _metadata = joblib.load(META_PATH)
        logger.info("Model loaded successfully.")
        logger.info(f"Model accuracy: {_metadata.get('accuracy', 'N/A')}%")
        return True
    except Exception as exc:
        logger.error(f"Failed to load model: {exc}")
        return False


load_model()

# ---------------------------------------------------------------------------
# Text preprocessing (mirrors train_model.py)
# ---------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Clean and normalise input text before prediction."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\d+", " ", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
    return " ".join(tokens)

# ---------------------------------------------------------------------------
# History helpers
# ---------------------------------------------------------------------------
def _load_history() -> list:
    """Load prediction history from JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_history(history: list) -> None:
    """Persist prediction history to JSON file."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def _append_to_history(entry: dict) -> None:
    """Append a single prediction entry to history."""
    history = _load_history()
    history.insert(0, entry)          # newest first
    history = history[:500]           # keep last 500
    _save_history(history)

# ---------------------------------------------------------------------------
# Explanation generator
# ---------------------------------------------------------------------------
def generate_explanation(label: str, confidence: float, text: str) -> str:
    """Generate a human-readable explanation for the prediction."""
    word_count = len(text.split())

    if label == "FAKE":
        if confidence >= 90:
            return (
                f"This article shows very strong indicators of misinformation. "
                f"The language patterns, writing style, and content structure "
                f"closely match known fake news articles in our training dataset. "
                f"The model is {confidence:.1f}% confident this is fabricated content."
            )
        elif confidence >= 75:
            return (
                f"This article contains several hallmarks of misleading content. "
                f"Our analysis of {word_count} words detected patterns common in "
                f"disinformation campaigns. Confidence level: {confidence:.1f}%."
            )
        else:
            return (
                f"This article has some characteristics of fake news, though the "
                f"signals are mixed. We recommend cross-checking with reputable "
                f"sources. Confidence: {confidence:.1f}%."
            )
    else:  # REAL
        if confidence >= 90:
            return (
                f"This article exhibits strong markers of credible journalism. "
                f"The writing style, vocabulary, and structure are consistent "
                f"with verified news sources. Confidence: {confidence:.1f}%."
            )
        elif confidence >= 75:
            return (
                f"This article appears to be legitimate news content based on "
                f"language patterns and structural analysis of {word_count} words. "
                f"Confidence: {confidence:.1f}%."
            )
            return (
                f"This article leans toward being real news, but the confidence "
                f"level is moderate ({confidence:.1f}%). Consider verifying with "
                f"additional sources."
            )

# ---------------------------------------------------------------------------
# TruthLens Hybrid Verification Pipeline Helpers
# ---------------------------------------------------------------------------

def extract_claim(text: str) -> str:
    """
    Extract the main claim/query keywords from the news text.
    Uses sentence tokenization and stops words removal to formulate
    a search query under 12 words.
    """
    if not text:
        return ""
    # Split into sentences using simple punctuation split to avoid heavy imports
    sents = [s.strip() for s in re.split(r'[.!?\n]+', text) if s.strip()]
    if not sents:
        return text[:100]
    
    # Take the first substantial sentence
    claim_candidate = sents[0]
    if len(claim_candidate) < 20 and len(sents) > 1:
        claim_candidate = claim_candidate + " " + sents[1]
        
    # Clean the claim candidate for search query
    claim_clean = re.sub(r'[^\w\s-]', '', claim_candidate)
    words = claim_clean.split()
    
    # Filter out stopwords
    filtered_words = [w for w in words if w.lower() not in STOP_WORDS]
    if not filtered_words:
        filtered_words = words
        
    # Keep up to 10 words
    query = " ".join(filtered_words[:10])
    return query

def perform_web_search(query: str) -> list:
    """
    Run real-time search for the claim query.
    Tries Google Custom Search API if key is available in environment variables,
    otherwise falls back to free DuckDuckGo Search.
    """
    if not query:
        return []
        
    google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    google_cx = os.getenv("GOOGLE_SEARCH_CX")
    
    # ── Try Google Custom Search first ──
    if google_api_key and google_cx:
        try:
            logger.info(f"Performing Google Search query: {query}")
            safe_query = urllib.parse.quote(query)
            url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={google_cx}&q={safe_query}&num=5"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", ""),
                        "href": item.get("link", ""),
                        "body": item.get("snippet", "")
                    })
                logger.info(f"Google Search returned {len(results)} results")
                return results
        except Exception as exc:
            logger.warning(f"Google Search API failed: {exc}. Falling back to DuckDuckGo.")
            
    # ── Fallback to DuckDuckGo ──
    try:
        logger.info(f"Performing DuckDuckGo Search query: {query}")
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        # Retrieve up to 5 results
        ddgs_results = list(DDGS().text(query, max_results=5))
        results = []
        for r in ddgs_results:
            results.append({
                "title": r.get("title", ""),
                "href": r.get("href", ""),
                "body": r.get("body", "")
            })
        logger.info(f"DuckDuckGo Search returned {len(results)} results")
        return results
    except Exception as exc:
        logger.error(f"Web search failed completely: {exc}")
        # Return None to indicate network/search service failure rather than empty results
        return None

def get_domain(url: str) -> str:
    """Extract and normalize domain name from URL."""
    try:
        netloc = urllib.parse.urlparse(url).netloc
        if not netloc:
            return ""
        # Remove www. and subdomains
        netloc = netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""

def analyze_source_credibility(url: str) -> dict:
    """
    Evaluate domain credibility based on known authoritative,
    satirical, and tabloid publisher mappings.
    """
    domain = get_domain(url)
    if not domain:
        return {"score": 0.7, "status": "neutral", "label": "Unknown Source"}
        
    HIGH_CREDIBILITY = [
        "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "nytimes.com",
        "washingtonpost.com", "wsj.com", "bloomberg.com", "theguardian.com",
        "npr.org", "pbs.org", "factcheck.org", "snopes.com", "politifact.com",
        "wikipedia.org", "nasa.gov", "cdc.gov", "who.int", "nih.gov"
    ]
    
    SATIRE_CREDIBILITY = [
        "theonion.com", "babylonbee.com", "clickhole.com", "newsthump.com",
        "thedailymash.co.uk", "theburrardstreetjournal.com", "waterfordwhispersnews.com"
    ]
    
    LOW_CREDIBILITY = [
        "dailymail.co.uk", "nypost.com", "foxnews.com", "rt.com", "infowars.com",
        "breitbart.com", "naturalnews.com", "worldnewsdailyreport.com", "nationalenquirer.com"
    ]
    
    # Suffix matching
    if any(domain == h or domain.endswith("." + h) for h in HIGH_CREDIBILITY) or domain.endswith(".gov") or domain.endswith(".edu"):
        return {"score": 1.0, "status": "high", "label": "Authoritative / Fact-Checker"}
        
    if any(domain == s or domain.endswith("." + s) for s in SATIRE_CREDIBILITY):
        return {"score": 0.0, "status": "satire", "label": "Satire / Humor Website"}
        
    if any(domain == l or domain.endswith("." + l) for l in LOW_CREDIBILITY):
        return {"score": 0.3, "status": "low", "label": "Tabloid / Hyper-Partisan"}
        
    return {"score": 0.7, "status": "neutral", "label": "General Media"}

def evaluate_evidence(claim_words: list, snippet: str) -> str:
    """
    Evaluate if a search result snippet supports, contradicts, or is neutral
    regarding the extracted claim keywords.
    """
    content = snippet.lower()
    
    # Contradiction keywords
    CONTRADICT_WORDS = [
        "debunk", "false", "fake", "untrue", "misleading", "hoax", "rumor",
        "incorrect", "exaggerated", "myth", "deny", "denies", "refute", "refutes",
        "contradict", "fabricated", "conspiracy", "debunked", "unverified"
    ]
    
    # Support keywords
    SUPPORT_WORDS = [
        "confirm", "confirms", "true", "correct", "accurate", "verify", "verifies",
        "validated", "proved", "proven", "report", "reports", "announced",
        "official", "factual", "valid", "authenticate", "established"
    ]
    
    # Count overlap of query words in snippet to check relevance
    query_overlap = sum(1 for w in claim_words if w.lower() in content)
    relevance_threshold = max(1, len(claim_words) // 4)
    
    if query_overlap < relevance_threshold:
        return "NEUTRAL"
        
    has_contradict = any(cw in content for cw in CONTRADICT_WORDS)
    has_support = any(sw in content for sw in SUPPORT_WORDS)
    
    if has_contradict and not has_support:
        return "CONTRADICTS"
    elif has_support and not has_contradict:
        return "SUPPORTS"
        
    return "NEUTRAL"


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Home / landing page."""
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    """Dashboard with statistics and charts."""
    return render_template("dashboard.html")


@app.route("/history")
def history_page():
    """Prediction history page."""
    return render_template("history.html")


@app.route("/about")
def about():
    """About page."""
    return render_template("about.html")


@app.route("/contact")
def contact():
    """Contact page."""
    return render_template("contact.html")

# ---------------------------------------------------------------------------
# API — Prediction
# ---------------------------------------------------------------------------
@app.route("/api/predict", methods=["POST"])
def predict():
    """
    POST /api/predict
    Body: { "text": "<news article text>" }
    Returns: advanced hybrid news verification results.
    """
    if _model is None or _vectorizer is None:
        return jsonify({
            "error": "Model not loaded. Please run: python train_model.py"
        }), 503

    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field in request body."}), 400

    raw_text = data["text"].strip()
    if len(raw_text) < 20:
        return jsonify({
            "error": "Text is too short. Please provide at least 20 characters."
        }), 400
    if len(raw_text) > 100_000:
        return jsonify({"error": "Text exceeds maximum length of 100,000 characters."}), 400

    start_time = time.perf_counter()

    # 1. Base ML model prediction
    cleaned = clean_text(raw_text)
    vectorised = _vectorizer.transform([cleaned])
    proba = _model.predict_proba(vectorised)[0]      # [P(real), P(fake)]
    pred_class = int(_model.predict(vectorised)[0])   # 0=Real, 1=Fake

    ml_label = "FAKE" if pred_class == 1 else "REAL"
    ml_confidence = round(float(proba[pred_class]) * 100, 2)
    fake_prob = round(float(proba[1]) * 100, 2)
    real_prob = round(float(proba[0]) * 100, 2)

    # 2. Real-time Web Verification
    claim_query = extract_claim(raw_text)
    claim_words = claim_query.split()
    search_results = perform_web_search(claim_query)

    sources_checked = []
    supporting_evidence = []
    contradicting_evidence = []
    
    # Defaults
    web_status = "Live verification unavailable"
    web_score = 0.5
    verdict = "UNVERIFIED"
    final_confidence = ml_confidence

    if search_results is None:
        # Search failed completely / offline
        web_status = "Live verification unavailable"
        if ml_label == "REAL":
            if ml_confidence >= 90:
                verdict = "UNVERIFIED" # Rules say never label true merely because model is Real
            else:
                verdict = "UNVERIFIED"
        else:
            if ml_confidence >= 90:
                verdict = "UNVERIFIED" # Strict guideline
            else:
                verdict = "UNVERIFIED"
        web_status_label = "Live verification unavailable (Model-only prediction)"
        final_confidence = ml_confidence
    else:
        # Search succeeded (can have 0 to 5 results)
        if not search_results:
            web_status = "No reliable current evidence found"
            verdict = "UNVERIFIED"
            web_status_label = "Not enough reliable evidence was found to determine whether this claim is true or false"
            web_score = 0.5
            final_confidence = 50.0
        else:
            # Evaluate each search result
            support_sum = 0.0
            contradict_sum = 0.0

            for idx, r in enumerate(search_results):
                cred = analyze_source_credibility(r["href"])
                evaluation = evaluate_evidence(claim_words, r["body"] + " " + r["title"])
                domain = get_domain(r["href"])
                
                # Check for dates in snippet
                date_match = re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:,\s+\d{4})?\b', r["body"], re.IGNORECASE)
                pub_date = date_match.group(0) if date_match else "Recent"

                source_item = {
                    "id": idx + 1,
                    "title": r["title"],
                    "url": r["href"],
                    "domain": domain,
                    "snippet": r["body"],
                    "credibility": cred["score"],
                    "credibility_label": cred["label"],
                    "evaluation": evaluation,
                    "pub_date": pub_date
                }
                sources_checked.append(source_item)

                if evaluation == "SUPPORTS":
                    support_sum += cred["score"]
                    supporting_evidence.append(source_item)
                elif evaluation == "CONTRADICTS":
                    contradict_sum += cred["score"]
                    contradicting_evidence.append(source_item)

            # Calculate web verification score
            if support_sum == 0.0 and contradict_sum == 0.0:
                web_score = 0.5
                web_status = "Insufficient evidence"
                web_status_label = "Not enough reliable evidence was found to verify this claim"
                verdict = "UNVERIFIED"
                final_confidence = 50.0
            else:
                raw_web = (support_sum - contradict_sum) / (support_sum + contradict_sum)
                web_score = (raw_web + 1.0) / 2.0
                
                if raw_web > 0.25:
                    verdict = "LIKELY TRUE"
                    web_status = "Strong support found"
                    web_status_label = "Live search found multiple reliable sources supporting this claim"
                elif raw_web < -0.25:
                    verdict = "LIKELY FALSE"
                    web_status = "Strong contradiction found"
                    web_status_label = "Live search found reliable sources contradicting this claim"
                else:
                    verdict = "UNVERIFIED"
                    web_status = "Conflicting reports found"
                    web_status_label = "Available evidence from live searches is conflicting or inconclusive"

                # Calculate final confidence (weighted 35% ML + 65% Web)
                ml_score_contrib = 1.0 if ml_label == "REAL" else 0.0
                combined_val = 0.35 * (ml_confidence / 100.0) * ml_score_contrib + 0.65 * web_score
                
                if verdict == "LIKELY TRUE":
                    final_confidence = round(max(50.0, combined_val * 100.0), 2)
                elif verdict == "LIKELY FALSE":
                    final_confidence = round(max(50.0, (1.0 - combined_val) * 100.0), 2)
                else:
                    final_confidence = 50.0

    # 3. Create Explanation
    if verdict == "LIKELY TRUE":
        explanation = f"TruthLens classified this claim as Likely True. The ML model detected language patterns associated with real news ({ml_confidence}% confidence), and real-time web searches verified the claim with supporting evidence from reputable sources."
    elif verdict == "LIKELY FALSE":
        explanation = f"TruthLens classified this claim as Likely False. While the ML model evaluated the text style, real-time web searches identified multiple authoritative sources that contradict the claim."
    else:
        explanation = "TruthLens marked this claim as Unverified. The current web-based evidence is either conflicting, insufficient, or unavailable to make a definitive determination. Further manual verification is recommended."

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # 4. Build Response Json
    result = {
        "id":                     str(uuid.uuid4()),
        "verdict":                verdict,
        "label":                  verdict,  # kept for legacy frontend support
        "confidence":             final_confidence,
        "ml_label":               ml_label,
        "ml_confidence":          ml_confidence,
        "fake_prob":              fake_prob,
        "real_prob":              real_prob,
        "claim_query":            claim_query,
        "web_status":             web_status,
        "web_status_label":       web_status_label if 'web_status_label' in locals() else web_status,
        "sources_checked":        sources_checked,
        "supporting_evidence":    supporting_evidence,
        "contradicting_evidence": contradicting_evidence,
        "explanation":            explanation,
        "prediction_ms":          elapsed_ms,
        "word_count":             len(raw_text.split()),
        "char_count":             len(raw_text),
        "timestamp":              datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
        "last_verified":          datetime.datetime.now(datetime.timezone.utc).strftime("%d-%b-%Y %H:%M:%S UTC"),
        "text_preview":           raw_text[:200] + ("…" if len(raw_text) > 200 else ""),
    }

    # Save to history
    _append_to_history(result)

    logger.info(
        f"Verdict: {verdict} ({final_confidence}%) | {web_status} | {elapsed_ms}ms"
    )

    return jsonify(result), 200

# ---------------------------------------------------------------------------
# API — History
# ---------------------------------------------------------------------------
@app.route("/api/history", methods=["GET"])
def get_history():
    """GET /api/history — Return all prediction history entries."""
    history = _load_history()
    return jsonify({
        "history": history,
        "total":   len(history),
    }), 200


@app.route("/api/history/<string:entry_id>", methods=["DELETE"])
def delete_history_entry(entry_id: str):
    """DELETE /api/history/<id> — Remove a single history entry."""
    history = _load_history()
    original_len = len(history)
    history = [h for h in history if h.get("id") != entry_id]

    if len(history) == original_len:
        return jsonify({"error": "Entry not found."}), 404

    _save_history(history)
    return jsonify({"message": "Entry deleted.", "id": entry_id}), 200


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    """DELETE /api/history — Clear all prediction history."""
    _save_history([])
    return jsonify({"message": "History cleared."}), 200

# ---------------------------------------------------------------------------
# API — Statistics (for dashboard)
# ---------------------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
def get_stats():
    """
    GET /api/stats — Return aggregated statistics for the dashboard.
    """
    history = _load_history()

    total      = len(history)
    fake_count = sum(1 for h in history if h.get("verdict") == "LIKELY FALSE" or h.get("label") == "FAKE")
    real_count = sum(1 for h in history if h.get("verdict") == "LIKELY TRUE" or h.get("label") == "REAL")
    unverified_count = sum(1 for h in history if h.get("verdict") == "UNVERIFIED")

    # Daily trend (last 7 days)
    today = datetime.datetime.now(datetime.timezone.utc).date()
    daily: dict[str, dict] = {}
    for i in range(7):
        day = (today - datetime.timedelta(days=i)).isoformat()
        daily[day] = {"fake": 0, "real": 0, "unverified": 0}

    for h in history:
        ts = h.get("timestamp", "")
        try:
            day_str = ts[:10]
            if day_str in daily:
                v = h.get("verdict") or h.get("label")
                if v in ["LIKELY FALSE", "FAKE"]:
                    daily[day_str]["fake"] += 1
                elif v in ["LIKELY TRUE", "REAL"]:
                    daily[day_str]["real"] += 1
                else:
                    daily[day_str]["unverified"] += 1
        except Exception:
            pass

    # Average confidence
    confidences = [h.get("confidence", 0) for h in history]
    avg_conf    = round(sum(confidences) / len(confidences), 2) if confidences else 0

    return jsonify({
        "total_predictions": total,
        "fake_count":        fake_count,
        "real_count":        real_count,
        "unverified_count":  unverified_count,
        "avg_confidence":    avg_conf,
        "model_accuracy":    _metadata.get("accuracy", "N/A"),
        "training_samples":  _metadata.get("total_samples", "N/A"),
        "daily_trend":       daily,
        "recent":            history[:5],
    }), 200


# ---------------------------------------------------------------------------
# API — Health check
# ---------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    """GET /api/health — Basic health check endpoint."""
    return jsonify({
        "status":       "ok",
        "model_loaded": _model is not None,
        "timestamp":    datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
    }), 200


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found."}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error."}), 500


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    logger.info(f"Starting Fake News Detector on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
