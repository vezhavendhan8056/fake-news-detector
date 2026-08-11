# 🔮 TruthLens — AI-Powered Information Verification Platform

> A premium, production-quality web application for detecting fake news and verifying information using NLP and Machine Learning — B.Sc. Computer Science Mini Project

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0+-green?style=flat-square&logo=flask)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.5+-orange?style=flat-square)
![Accuracy](https://img.shields.io/badge/Accuracy-98%25+-brightgreen?style=flat-square)

---

## 🌟 Features

- **Real-time Detection** — Analyse any news article in under 100ms
- **Confidence Score** — Detailed probability breakdown for real/fake
- **AI Explanation** — Human-readable explanation for each prediction
- **Dashboard** — Visual analytics with Chart.js charts
- **History** — Browse, search, filter, and export prediction history
- **Dark/Light Mode** — Full theme switching
- **Responsive Design** — Works on all devices
- **Copy & PDF Export** — Save or share results
- **Sample Articles** — Built-in sample real/fake news for testing

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python Flask |
| ML | Scikit-learn, TF-IDF, Logistic Regression |
| NLP | NLTK (stopwords, tokenisation) |
| Data | Pandas, NumPy |
| Charts | Chart.js |
| Persistence | Joblib, JSON |

---

## 📂 Project Structure

```
fake-news-detector/
│
├── app.py                  # Flask application (REST API + routes)
├── train_model.py          # ML training pipeline
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
├── model/                  # Saved ML model files
│   ├── model.pkl           # Trained Logistic Regression
│   ├── vectorizer.pkl      # Fitted TF-IDF vectorizer
│   └── metadata.pkl        # Training metadata & accuracy
│
├── dataset/                # Training data (place CSV files here)
│   ├── Fake.csv
│   └── True.csv
│
├── templates/              # Jinja2 HTML templates
│   ├── index.html          # Home / detector page
│   ├── dashboard.html      # Analytics dashboard
│   ├── history.html        # Prediction history
│   ├── about.html          # About page
│   └── contact.html        # Contact page
│
├── static/
│   ├── css/
│   │   └── style.css       # Design system (dark/light mode)
│   ├── js/
│   │   ├── main.js         # Shared utilities
│   │   ├── detector.js     # Detector page logic
│   │   ├── dashboard.js    # Dashboard charts
│   │   └── history.js      # History management
│   └── images/
│
└── saved_predictions/
    └── history.json        # Prediction history (auto-created)
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- `pip` package manager

### 2. Clone / Download
```bash
git clone https://github.com/yourusername/fake-news-detector.git
cd fake-news-detector
```

### 3. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Add Dataset
Place `Fake.csv` and `True.csv` inside the `dataset/` folder.

You can download the dataset from:
> https://www.kaggle.com/clmentbisaillon/fake-and-real-news-dataset

### 6. Train the Model
```bash
python train_model.py
```
This will train the model and save it to the `model/` directory.

### 7. Run the Application
```bash
python app.py
```

Open your browser and visit: **http://127.0.0.1:5000**

---

## 🔌 API Reference

### POST /api/predict
Analyse a news article.

**Request:**
```json
{
  "text": "Your news article text here..."
}
```

**Response:**
```json
{
  "id": "uuid",
  "label": "FAKE | REAL",
  "confidence": 94.3,
  "fake_prob": 94.3,
  "real_prob": 5.7,
  "explanation": "AI explanation...",
  "prediction_ms": 45.2,
  "word_count": 150,
  "char_count": 1200,
  "timestamp": "2024-01-01T00:00:00Z",
  "text_preview": "First 200 chars..."
}
```

### GET /api/stats
Dashboard statistics.

### GET /api/history
All prediction history.

### DELETE /api/history/:id
Delete a single entry.

### DELETE /api/history
Clear all history.

### GET /api/health
Health check.

---

## 🤖 ML Pipeline

1. **Data Loading** — Load Fake.csv and True.csv, assign labels
2. **Text Combination** — Merge title + text for richer features
3. **Preprocessing** — Lowercase, remove URLs/HTML/punctuation, stopword removal
4. **Train/Test Split** — 80% training, 20% testing (stratified)
5. **TF-IDF Vectorisation** — 50,000 features, unigrams + bigrams
6. **Logistic Regression** — C=1.0, max_iter=1000, lbfgs solver
7. **Evaluation** — Accuracy, classification report, confusion matrix
8. **Persistence** — Save model, vectorizer, metadata with Joblib

---

## 🌐 Deployment on Render

1. Push your project to GitHub
2. Go to [render.com](https://render.com) and create a new **Web Service**
3. Connect your GitHub repository
4. Set the following:
   - **Build Command:** `pip install -r requirements.txt && python train_model.py`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3

**Note:** Upload the dataset files or train the model locally and commit the `model/` directory.

---

## 📜 License

MIT License — Free for educational and personal use.

---

## 🙏 Acknowledgements

- Dataset: [Kaggle Fake and Real News Dataset](https://www.kaggle.com/clmentbisaillon/fake-and-real-news-dataset)
- ML: [Scikit-learn](https://scikit-learn.org)
- NLP: [NLTK](https://www.nltk.org)
- Charts: [Chart.js](https://www.chartjs.org)

---

*Built with ❤️ for B.Sc. Computer Science Mini Project*
