# 🎯 ATS Resume Analyzer

An AI-powered Applicant Tracking System (ATS) Resume Analyzer built with Django and Google Gemini API. Upload your resume, paste a job description, and get a detailed score, skill gap analysis, improvement suggestions, and an AI-rewritten optimized resume.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-4.x-green)
![Gemini](https://img.shields.io/badge/Gemini-2.5--flash-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🚀 Live Demo

> [https://ats-analyzer.onrender.com](https://ats-analyzer.onrender.com)

---

## ✨ Features

- **ATS Score** — Weighted score across 5 dimensions: Skill Match, Keywords, Experience, Education, Format
- **Skill Gap Analysis** — Identifies missing skills with difficulty level, learning time, and resources
- **AI Suggestions** — Rule-based + Gemini-powered improvement suggestions
- **AI Resume Rewriter** — Full resume rewrite optimized for the target job
- **Chart.js Dashboard** — Radar chart, bar chart, doughnut chart, progress rings
- **PDF & DOCX Export** — Download the optimized resume instantly
- **5-Tab Interface** — Overview, Dashboard, Skill Gaps, Suggestions, Rewriter

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Django 4.x |
| AI | Google Gemini 2.5 Flash |
| NLP | spaCy, sentence-transformers |
| Resume Parsing | pdfplumber, python-docx |
| Export | ReportLab (PDF), python-docx (DOCX) |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Database | SQLite (dev), PostgreSQL (prod) |
| File Storage | Cloudinary (prod) |
| Deployment | Render / Railway |

---

## 📸 Screenshots

### Upload Page
Clean dark-themed upload form with resume + job description input.

### Results Dashboard
5-tab results page with score breakdown, charts, and AI insights.

### AI Rewriter
Full resume rewrite with before/after comparison and download buttons.

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- Git
- Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone the repository
```bash
git clone https://github.com/hashikmagesh/ats-analyzer.git
cd ats-analyzer
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Create `.env` file
```bash
# Create .env in project root
SECRET_KEY=your-django-secret-key
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Create admin user (optional)
```bash
python manage.py createsuperuser
```

### 7. Start the server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` 🎉

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ Yes | Django secret key |
| `DEBUG` | ✅ Yes | `True` for dev, `False` for prod |
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key |
| `DATABASE_URL` | Production | PostgreSQL URL (auto-set by Render/Railway) |
| `CLOUDINARY_CLOUD_NAME` | Production | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Production | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Production | Cloudinary API secret |

---

## 🧠 How It Works

```
User uploads resume (PDF/DOCX)
           │
           ▼
    Text Extraction (pdfplumber / python-docx)
           │
           ▼
    Section Detection (NLP — 8 sections)
           │
           ▼
    Skill Extraction (spaCy + database matching)
           │
           ▼
    JD Analysis (required skills, keywords, level)
           │
           ▼
    Semantic Matching (sentence-transformers)
           │
           ▼
    ATS Scoring (5-component weighted score)
           │
           ▼
    Skill Gap Analysis (difficulty, time, resources)
           │
           ▼
    AI Suggestions (Gemini-powered)
           │
           ▼
    AI Resume Rewriter (full rewrite via Gemini)
           │
           ▼
    Export PDF / DOCX
```

---

## 📊 ATS Score Breakdown

| Component | Weight | What It Measures |
|---|---|---|
| Skill Match | 30% | Resume skills vs JD requirements |
| Keyword Match | 25% | JD keywords found in resume |
| Experience | 20% | Years + relevance to role |
| Education | 15% | Degree level match |
| Format | 10% | Structure, length, action verbs |

---

## 🗂 Project Structure

```
ats_analyzer/
├── config/
│   ├── settings.py       # Django settings
│   ├── urls.py           # Root URL config
│   └── wsgi.py
├── analyzer/
│   ├── services/
│   │   ├── resume_extractor.py    # PDF/DOCX text extraction
│   │   ├── section_detector.py    # Resume section detection
│   │   ├── jd_analyzer.py         # Job description analysis
│   │   ├── skill_extractor.py     # NLP skill extraction
│   │   ├── semantic_matcher.py    # Skill matching
│   │   ├── ats_scorer.py          # ATS score calculation
│   │   ├── gap_analyzer.py        # Skill gap analysis
│   │   ├── ai_suggester.py        # AI suggestions
│   │   ├── resume_rewriter.py     # AI resume rewriter
│   │   └── resume_exporter.py     # PDF/DOCX export
│   ├── models.py          # Database models
│   ├── views.py           # Django views
│   ├── urls.py            # App URL config
│   └── forms.py           # Upload form
├── templates/
│   ├── base.html          # Base template
│   ├── upload.html        # Upload page
│   └── results.html       # Results dashboard
├── static/
│   ├── css/
│   └── js/
├── requirements.txt
├── Procfile
├── build.sh
└── README.md
```

---

## 🚀 Deployment (Render — Free)

### 1. Fork this repo

### 2. Create Cloudinary account
Get free keys at [cloudinary.com](https://cloudinary.com)

### 3. Create Render account
Sign up at [render.com](https://render.com) with GitHub

### 4. New Web Service on Render
- Connect your forked repo
- Build Command: `chmod +x build.sh && ./build.sh`
- Start Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

### 5. Add PostgreSQL on Render
New → PostgreSQL → Free tier → copy Internal Database URL

### 6. Add Environment Variables on Render
```
SECRET_KEY              = (generate with Django)
DEBUG                   = False
GEMINI_API_KEY          = your-key
DATABASE_URL            = (from PostgreSQL above)
CLOUDINARY_CLOUD_NAME   = your-cloud-name
CLOUDINARY_API_KEY      = your-api-key
CLOUDINARY_API_SECRET   = your-api-secret
```

### 7. Deploy 🎉

---

## 📝 API Keys Needed

| Service | Cost | Get It |
|---|---|---|
| Google Gemini | Free (15 req/min) | [aistudio.google.com](https://aistudio.google.com/apikey) |
| Cloudinary | Free (25GB) | [cloudinary.com](https://cloudinary.com/users/register_free) |

---

## 🧪 Running Tests

```bash
python test_extraction.py
python test_sections.py
python test_jd_analyzer.py
python test_skill_extractor.py
python test_semantic_matcher.py
python test_ats_scorer.py
python test_gap_analyzer.py
python test_suggestions.py
python test_rewriter.py
python test_exporter.py
python test_api_connection.py
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Hashik M**
- LinkedIn: [linkedin.com/in/hashik-magesh](https://linkedin.com/in/hashik-magesh)
- GitHub: [github.com/hashikmagesh](https://github.com/hashikmagesh)
- Email: hashikmagesh@gmail.com

---

## 🙏 Acknowledgements

- [Google Gemini](https://ai.google.dev/) — AI rewriting and suggestions
- [spaCy](https://spacy.io/) — NLP processing
- [sentence-transformers](https://www.sbert.net/) — Semantic skill matching
- [Chart.js](https://www.chartjs.org/) — Score visualizations
- [ReportLab](https://www.reportlab.com/) — PDF generation
- [Django](https://www.djangoproject.com/) — Web framework