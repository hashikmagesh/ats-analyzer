# test_ats_scorer.py
# Run with: python test_ats_scorer.py

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analyzer.services.ats_scorer import calculate_ats_score

resume_text = """
HASHIK M | hashikmagesh@gmail.com | +91-8098020104

SUMMARY
Python Full Stack Developer with 2 years of internship
experience in Django and MySQL. Built 3 production projects.

EXPERIENCE AND INTERNSHIP
Python Full Stack Developer — Smik Systems (2024)
- Engineered Django web apps improving response time by 30%
- Optimized MySQL queries and enhanced UI components
- Collaborated with teams to deliver high-performance solutions

Web Development Intern — NXTLogic (2023)
- Designed 5+ responsive websites using HTML, CSS
- Improved website performance by optimizing assets

SKILLS
Python, Django, MySQL, MongoDB, HTML, CSS, JavaScript, Git

EDUCATION
B.E. Computer Science — SNS College of Technology 2022-2026
CGPA: 7.6
"""

sections = {
    'summary':    'Python Full Stack Developer...',
    'experience': 'Python Full Stack Developer — Smik...',
    'skills':     'Python, Django, MySQL...',
    'education':  'B.E. Computer Science...',
    'projects':   '',
}

resume_skills = {
    'all_skills': ['Python', 'Django', 'MySQL', 'Git', 'HTML'],
    'technical_skills': ['Python', 'Django', 'MySQL'],
    'tools': ['Git'],
    'soft_skills': ['Leadership'],
}

jd_data = {
    'required_skills': ['Python', 'Django', 'PostgreSQL', 'Git'],
    'preferred_skills': ['Docker', 'AWS'],
    'experience_years': 1,
    'education_level':  'bachelors',
    'job_level':        'junior',
    'keywords': ['backend', 'scalable', 'agile', 'api'],
}

match_result = {
    'matched_required':  ['Python', 'Django', 'Git'],
    'missing_required':  ['PostgreSQL'],
    'matched_preferred': [],
    'required_score':    75.0,
    'preferred_score':   0.0,
    'overall_match':     63.75,
}

result = calculate_ats_score(
    resume_text, sections, resume_skills, jd_data, match_result
)

print("=" * 50)
print("     ATS SCORE RESULTS")
print("=" * 50)
print(f"\n🏆 Overall Score  : {result['overall_score']}/100")
print(f"📊 Grade          : {result['grade']} — {result['grade_label']}")
print(f"👔 Hire Likelihood: {result['hire_likelihood']}")
print(f"\n📈 Score Breakdown:")
print(f"   Skill Score      : {result['skill_score']}")
print(f"   Keyword Score    : {result['keyword_score']}")
print(f"   Experience Score : {result['experience_score']}")
print(f"   Education Score  : {result['education_score']}")
print(f"   Format Score     : {result['format_score']}")
print(f"\n💪 Strengths:")
for s in result['strengths']:
    print(f"   ✅ {s}")
print(f"\n⚠️  Weaknesses:")
for w in result['weaknesses']:
    print(f"   ❌ {w}")
print("\n✅ ATS Scorer working!")