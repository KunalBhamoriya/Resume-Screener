# Smart Resume Screening System — AI-Powered

An AI-powered system that matches resumes against a Job Description using **sentence-transformer embeddings**, returning ranked candidates with match scores, skill gap analysis, and plain-English explanations.

---

## Table of Contents

1. [Setup Steps](#setup-steps)
2. [How to Run the API](#how-to-run-the-api)
3. [Approach Explanation](#approach-explanation)

---

## Setup Steps

### Prerequisites

- Python **3.10 or higher**
- pip (comes with Python)
- Internet connection (to download the AI model on first run, ~80 MB)

---

### Windows

```powershell
# 1. Go to the project folder
cd e:\MXPERTZ_work\Resume_Screening

# 2. Create a virtual environment
python -m venv .venv

# 3. Allow running scripts (one-time fix for PowerShell)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4. Activate the virtual environment
.venv\Scripts\Activate.ps1

# 5. Install all dependencies
pip install -r requirements.txt
```

> **Tip (if activation fails):** You can skip activation and use `.venv\Scripts\pip` and `.venv\Scripts\uvicorn` directly instead.

---

### Linux / macOS

```bash
# 1. Go to the project folder
cd /path/to/Resume_Screening

# 2. Create a virtual environment
python3 -m venv .venv

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Install all dependencies
pip install -r requirements.txt
```

---

## How to Run the API

### Start the server

**Windows (venv activated):**
```powershell
uvicorn app.main:app --reload
```

**Windows (without activating venv):**
```powershell
.venv\Scripts\uvicorn app.main:app --reload
```

**Linux / macOS:**
```bash
uvicorn app.main:app --reload
```

The server starts at **http://127.0.0.1:8000**

> **Note:** On the very first startup, the AI model (`all-MiniLM-L6-v2`) is downloaded automatically. This takes ~1 minute once and is then cached permanently.

---

### Open the Web UI

Go to → **http://127.0.0.1:8000**

You will see a web interface where you can:
- Paste a Job Description
- Upload PDF resumes **or** paste resume text
- Click **Screen Resumes** to get ranked results

---

### API Docs (Interactive)

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000/docs | Swagger UI — try endpoints in the browser |
| http://127.0.0.1:8000/redoc | ReDoc — clean API documentation |
| http://127.0.0.1:8000/health | Health check |

---

### Run a Quick Demo (optional)

Make sure the server is running, then open a **second terminal** and run:

```bash
python sample_request.py
```

This sends 4 sample resumes against a sample JD and prints ranked results in the terminal.

---

### API Endpoint Reference

#### `POST /screen` — Screen resumes against a JD

**Request:**
```json
{
  "job_description": "We are looking for a Python engineer with FastAPI, PostgreSQL, Docker...",
  "resumes": [
    { "name": "Alice Johnson", "content": "5 years Python, FastAPI, Docker, AWS..." },
    { "name": "Bob Smith",     "content": "React, Node.js, MySQL developer..." }
  ]
}
```

**Response:**
```json
{
  "job_title_hint": "Python engineer",
  "total_resumes": 2,
  "results": [
    {
      "name": "Alice Johnson",
      "match_score": 87.3,
      "matched_skills": ["python", "fastapi", "docker", "aws"],
      "missing_skills": ["kubernetes"],
      "explanation": "Alice Johnson shows an excellent match (87.3/100)..."
    }
  ]
}
```

#### `POST /extract-pdf` — Extract text from a PDF resume

Upload a `.pdf` file and get back the extracted text (used automatically by the web UI).

---

## Approach Explanation

### The Problem

Traditional resume screening is keyword-based — it checks if exact words from the JD appear in the resume. This misses candidates who describe the same skill differently (e.g., *"ML engineer"* vs *"machine learning developer"*).

This system solves that using **semantic embeddings** — understanding the *meaning* of text, not just keywords.

---

### Step 1 — Skill Extraction

When a JD and resume arrive, the system first extracts skills using a curated vocabulary of **120+ tech skills** (Python, FastAPI, Docker, AWS, NLP, etc.) matched with regex.

- Skills from the JD = **required skills**
- Skills from the resume = **candidate skills**
- Overlap → **Matched Skills** and **Missing Skills**

This is fast, deterministic, and easy to extend.

---

### Step 2 — Embedding-Based Semantic Matching

Both the JD and each resume are converted into **384-dimensional numerical vectors** using the `all-MiniLM-L6-v2` model from Hugging Face.

```
"Senior Python engineer with FastAPI experience"
        ↓  (sentence-transformer model)
[0.021, -0.134, 0.087, ... ]  ← 384 numbers representing meaning
```

The model is pre-trained on millions of text pairs, so it understands that:
- *"machine learning"* ≈ *"ML"*
- *"cloud infrastructure"* ≈ *"AWS / GCP / Azure"*
- *"REST APIs"* ≈ *"backend web services"*

All resumes are embedded in a **single batch** (efficient), then **cosine similarity** is computed between the JD vector and each resume vector.

---

### Step 3 — Blended Scoring

The final score combines two signals:

```
Final Score = 70% × Semantic Score  +  30% × Skill Overlap Score
```

| Signal | Method | Weight | Why |
|--------|--------|--------|-----|
| **Semantic Score** | Cosine similarity of embeddings | 70% | Captures meaning, synonyms, context |
| **Skill Overlap** | F1 score of matched vs required skills | 30% | Ensures hard skill keywords are rewarded |

The **F1 skill score** is the harmonic mean of:
- **Recall** — what fraction of JD skills appear in the resume
- **Precision** — what fraction of resume skills are relevant to the JD

This penalises resumes that just dump every skill keyword without covering JD requirements.

---

### Step 4 — Explanation Generation

For each candidate, a 2–3 sentence explanation is auto-generated describing:
- The overall match tier (excellent / good / moderate / low)
- Top matched skills
- Key missing skills
- Experience gap (if years of experience is mentioned)

---

### Why `all-MiniLM-L6-v2`?

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| all-MiniLM-L6-v2 ✅ | ~80 MB | Very fast (CPU-friendly) | High |
| all-mpnet-base-v2 | ~420 MB | Slower | Higher |
| OpenAI embeddings | Cloud API | Fast | Very High |

`all-MiniLM-L6-v2` is the best balance for a local, CPU-only deployment.

---

### Project Structure

```
Resume_Screening/
├── app/
│   ├── main.py        → FastAPI app, /screen and /extract-pdf endpoints
│   ├── models.py      → Pydantic request/response schemas
│   ├── extractor.py   → Skill & experience extraction (regex + vocab)
│   └── screener.py    → Embedding engine + blended scoring
├── static/
│   └── index.html     → Web UI (PDF upload + results display)
├── tests/
│   └── test_screener.py → Pytest test suite
├── sample_request.py  → Demo script with 4 sample resumes
├── requirements.txt
└── README.md
```
