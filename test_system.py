# =============================================================================
# test_system.py — TruthLens Evaluation Test Framework
# Evaluates classification metrics from actual test claims.
# =============================================================================

import os
import sys
import logging
import numpy as np

# Suppress flask logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import app

# Verify model loaded
if not app.load_model():
    print("Error: Could not load the ML model. Please run 'python train_model.py' first.")
    sys.exit(1)

# Test cases with diverse news categories
# Label mapping:
# 0 = REAL (Likely True)
# 1 = FAKE (Likely False)
# 2 = UNVERIFIED (Needs verification / conflicting / unknown / satire)
TEST_SUITE = [
    # ── Real News (Ground Truth: REAL) ──
    {
        "text": "NASA Scientists Confirm Water Ice on Moon's Surface. The findings, published in the journal Nature Astronomy, show that water ice is concentrated at the lunar poles in permanently shadowed regions. This discovery could have significant implications for future moon missions.",
        "expected": "LIKELY TRUE",
        "category": "Science"
    },
    {
        "text": "The Federal Reserve raised its benchmark interest rate by a quarter percentage point on Wednesday, bringing the federal funds rate to a range of 5.25 to 5.5 percent, the highest level in 22 years.",
        "expected": "LIKELY TRUE",
        "category": "Economy"
    },
    {
        "text": "The World Health Organization declared an end to the COVID-19 public health emergency of international concern on Thursday, marking a symbolic turning point in the pandemic that has killed millions.",
        "expected": "LIKELY TRUE",
        "category": "Health"
    },
    {
        "text": "Electric vehicle sales exceeded 10 million units worldwide for the first time in a single year, according to data released by the International Energy Agency, driven by high demand in China and Europe.",
        "expected": "LIKELY TRUE",
        "category": "Technology"
    },

    # ── False News (Ground Truth: FAKE) ──
    {
        "text": "SHOCKING REVELATION: Scientists at a secret government laboratory have discovered that a common kitchen ingredient can cure all known diseases including cancer, diabetes, HIV, and COVID-19. The miracle cure involves drinking baking soda with apple cider vinegar.",
        "expected": "LIKELY FALSE",
        "category": "Health / Conspiracies"
    },
    {
        "text": "COVID-19 Vaccine Contains Microchips That Allow Bill Gates to Track You. Anonymous doctors confirm the chips are activated by 5G towers to monitor your every move. Metal objects stick to the vaccination site.",
        "expected": "LIKELY FALSE",
        "category": "Conspiracies"
    },
    {
        "text": "URGENT: 5G Towers Are Actually Directed Energy Weapons designed to kill people who resist the New World Order. Pentagon documents show frequencies cause sudden cardiac arrest in targeted individuals.",
        "expected": "LIKELY FALSE",
        "category": "Conspiracies"
    },
    {
        "text": "Evidence has emerged proving that Democrats have programmed voting machines in swing states to switch Republican votes. A computer security expert found hidden code that activates on election day.",
        "expected": "LIKELY FALSE",
        "category": "Politics"
    },

    # ── Satirical & Unverified Claims (Ground Truth: UNVERIFIED) ──
    {
        "text": "The Onion: Nation's Scientists Warn Liquid Core Of Earth Actually Just Prego Marinara Sauce. Geologists confirm plate tectonics are driven by slow-simmering garlic and herbs.",
        "expected": "UNVERIFIED",
        "category": "Satire"
    },
    {
        "text": "Local community center in a small village to host a fundraiser bake sale tomorrow morning, featuring homemade chocolate chip cookies and apple pies.",
        "expected": "UNVERIFIED",
        "category": "Local News / Insufficient Evidence"
    },
    {
        "text": "BOMBSHELL: Stanley Kubrick confessed to staging the 1969 Apollo moon landing in a Hollywood studio, using Icelandic rocks as props. NASA contractors were silenced.",
        "expected": "LIKELY FALSE", # Or unverified since it's debunked
        "category": "Conspiracies"
    },
    {
        "text": "A new species of glowing purple jellyfish has allegedly been spotted in a swimming pool in a private backyard in suburban Houston yesterday.",
        "expected": "UNVERIFIED",
        "category": "Unverified Claim"
    }
]

def run_evaluation():
    print("=" * 60)
    print("       TruthLens System Evaluation & Test Framework")
    print("=" * 60)
    print(f"Running test suite on {len(TEST_SUITE)} diverse claims...\n")

    y_true = []
    y_pred = []
    
    hits = 0

    for idx, case in enumerate(TEST_SUITE):
        print(f"[{idx+1:02d}] Category: {case['category']}")
        print(f"     Claim Preview: {case['text'][:70]}...")
        
        # Simulate prediction logic directly
        raw_text = case["text"]
        
        # ML Prediction
        cleaned = app.clean_text(raw_text)
        vectorised = app._vectorizer.transform([cleaned])
        proba = app._model.predict_proba(vectorised)[0]
        pred_class = int(app._model.predict(vectorised)[0])
        ml_label = "FAKE" if pred_class == 1 else "REAL"
        ml_confidence = proba[pred_class] * 100
        
        # Web Search
        claim_query = app.extract_claim(raw_text)
        search_results = app.perform_web_search(claim_query)
        
        verdict = "UNVERIFIED"
        web_status = "No results"
        
        if search_results:
            support_sum = 0
            contradict_sum = 0
            claim_words = claim_query.split()
            
            for r in search_results:
                cred = app.analyze_source_credibility(r["href"])
                evaluation = app.evaluate_evidence(claim_words, r["body"] + " " + r["title"])
                if evaluation == "SUPPORTS":
                    support_sum += cred["score"]
                elif evaluation == "CONTRADICTS":
                    contradict_sum += cred["score"]
            
            if support_sum > 0 or contradict_sum > 0:
                raw_web = (support_sum - contradict_sum) / (support_sum + contradict_sum)
                if raw_web > 0.25:
                    verdict = "LIKELY TRUE"
                    web_status = "Web Supports"
                elif raw_web < -0.25:
                    verdict = "LIKELY FALSE"
                    web_status = "Web Contradicts"
                else:
                    verdict = "UNVERIFIED"
                    web_status = "Conflicting"
            else:
                verdict = "UNVERIFIED"
                web_status = "Insufficient"
        else:
            verdict = "UNVERIFIED"
            web_status = "Search Unavailable / Empty"
            
        print(f"     ML predicted: {ml_label} ({ml_confidence:.1f}%)")
        print(f"     Web evidence: {web_status}")
        print(f"     Final Verdict: {verdict} (Expected: {case['expected']})")
        
        y_true.append(case["expected"])
        y_pred.append(verdict)
        
        if verdict == case["expected"]:
            hits += 1
            print("     Result: SUCCESS [OK]")
        else:
            # Check if likely false and expected likely false, which are correct
            print("     Result: MISMATCH [X]")
        print("-" * 50)

    # Calculate metrics
    accuracy = hits / len(TEST_SUITE)
    
    print("\n" + "=" * 60)
    print("                 Evaluation Metrics")
    print("=" * 60)
    print(f"Total Test Claims   : {len(TEST_SUITE)}")
    print(f"Correct Predictions  : {hits}")
    print(f"System Accuracy      : {accuracy * 100:.2f}%")
    print("-" * 60)
    print("Verdict Distribution (Predicted):")
    print(f"  LIKELY TRUE        : {y_pred.count('LIKELY TRUE')}")
    print(f"  LIKELY FALSE       : {y_pred.count('LIKELY FALSE')}")
    print(f"  UNVERIFIED         : {y_pred.count('UNVERIFIED')}")
    print("=" * 60)

if __name__ == "__main__":
    run_evaluation()
