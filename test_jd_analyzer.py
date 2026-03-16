# test_jd_analyzer.py
# Run with: python test_jd_analyzer.py

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analyzer.services.jd_analyzer import analyze_job_description

JD_TEXT = """
Software Engineer - Python Backend

About the Role:
We are looking for a mid-level Python Developer to join our
growing engineering team. You will build scalable REST APIs
and microservices that power our platform.

Requirements:
- 3+ years of experience with Python
- Strong knowledge of Django or FastAPI
- Experience with PostgreSQL and Redis
- Understanding of Docker and CI/CD pipelines
- Familiarity with AWS or GCP
- Good understanding of REST API design
- Experience with Git and GitHub
- Bachelor's degree in Computer Science or related field

Preferred:
- Experience with Kubernetes
- Knowledge of React or Vue.js
- Familiarity with GraphQL
- Experience with microservices architecture

Responsibilities:
- Build and maintain scalable backend services
- Write clean, testable code with unit testing
- Collaborate with frontend and DevOps teams
- Participate in agile/scrum ceremonies
"""

print("=" * 55)
print("     JD ANALYZER TEST")
print("=" * 55)

result = analyze_job_description(JD_TEXT)

print(f"\n📊 Total Skills Found : {result['total_skills_found']}")
print(f"⏱  Experience Years  : {result['experience_years']}+")
print(f"🎓 Education Level   : {result['education_level']}")
print(f"📈 Job Level         : {result['job_level']}")

print(f"\n🔴 Required Skills ({len(result['required_skills'])}):")
for s in result['required_skills']:
    print(f"   - {s}")

print(f"\n🟡 Preferred Skills ({len(result['preferred_skills'])}):")
for s in result['preferred_skills']:
    print(f"   - {s}")

print(f"\n🔵 Top Keywords:")
print(f"   {', '.join(result['keywords'][:10])}")

print(f"\n📂 Skills by Category:")
for cat, skills in result['skills_by_category'].items():
    print(f"   {cat}: {', '.join(skills)}")

print("\n" + "=" * 55)
print("✅ JD Analyzer working correctly!")
print("=" * 55)