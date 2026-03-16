# test_sections.py
# Run with: python test_sections.py

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analyzer.services.section_detector import SectionDetector

# ── Sample resume text ────────────────────────────────
SAMPLE_RESUME = """
John Doe
john.doe@email.com | +91-9999999999 | LinkedIn | GitHub

PROFESSIONAL SUMMARY
Results-driven Python Developer with 4 years of experience
building scalable web applications and REST APIs.

WORK EXPERIENCE
Senior Python Developer — TechCorp India (2022-Present)
- Built REST APIs using Django and FastAPI serving 1M+ users
- Reduced database query time by 40% using PostgreSQL indexing
- Led a team of 4 developers on microservices migration

Python Developer — StartupXYZ (2020-2022)
- Developed data pipelines using Apache Kafka and Spark
- Built ML models using scikit-learn and TensorFlow

TECHNICAL SKILLS
Languages   : Python, JavaScript, SQL
Frameworks  : Django, FastAPI, React
Databases   : PostgreSQL, MongoDB, Redis
Cloud/DevOps: AWS, Docker, Kubernetes, CI/CD
ML/AI       : TensorFlow, scikit-learn, Pandas, NumPy

EDUCATION
B.Tech in Computer Science
Indian Institute of Technology, Delhi — 2020
CGPA: 8.7/10

PROJECTS
ATS Resume Analyzer
- Built an AI-powered resume analyzer using Django and OpenAI
- Achieved 95% accuracy in skill matching

Stock Price Predictor
- LSTM-based model predicting stock prices with 87% accuracy

CERTIFICATIONS
- AWS Certified Solutions Architect (2023)
- Google Professional Data Engineer (2022)

ACHIEVEMENTS
- Winner, Smart India Hackathon 2021
- Published paper on NLP in IEEE conference
"""

# ── Run detection ─────────────────────────────────────
print("Running section detection on sample resume...\n")

detector = SectionDetector(SAMPLE_RESUME)
detector.print_sections()

# ── Also test individual section access ───────────────
sections = detector.detect()

print("\n📌 Quick access test:")
print(f"   Skills section    : "
      f"{sections['skills'][:60]}...")
print(f"   Education section : "
      f"{sections['education'][:60]}...")
print(f"   Experience section: "
      f"{sections['experience'][:60]}...")