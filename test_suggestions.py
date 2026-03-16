# test_suggestions.py
# Run with: python test_suggestions.py

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analyzer.services.ai_suggester import generate_suggestions

resume_text = """
HASHIK M
hashikmagesh@gmail.com | LinkedIn

EXPERIENCE AND INTERNSHIP
Python Full Stack Developer — Smik Systems (2024)
- Worked on Django web applications
- Helped with MySQL database
- Used Git for version control

Web Development Intern — NXTLogic (2023)
- Did HTML and CSS work
- Assisted with responsive design

SKILLS
Python, Django, MySQL, HTML, CSS, Git

EDUCATION
B.E. Computer Science — SNS College 2022-2026
"""

sections = {
    'summary':    '',
    'experience': (
        'Python Full Stack Developer — Smik Systems (2024)\n'
        '- Worked on Django web applications\n'
        '- Helped with MySQL database\n'
        '- Used Git for version control'
    ),
    'skills':     'Python, Django, MySQL, HTML, CSS, Git',
    'education':  'B.E. Computer Science — SNS College',
}
resume_skills = {
    'all_skills':       ['Python', 'Django', 'MySQL', 'Git'],
    'technical_skills': ['Python', 'Django', 'MySQL'],
    'tools':            ['Git'],
}
jd_data = {
    'required_skills':  ['Python', 'Django', 'REST API', 'Docker'],
    'preferred_skills': ['AWS'],
    'job_level':        'junior',
    'keywords':         ['scalable', 'agile', 'backend', 'api'],
}
match_result = {
    'matched_required': ['Python', 'Django'],
    'missing_required': ['REST API', 'Docker'],
    'overall_match':    50.0,
}
ats_score = {'overall_score': 55.0}

result = generate_suggestions(
    resume_text, sections, resume_skills,
    jd_data, match_result, ats_score
)

print("=" * 55)
print("     SUGGESTION ENGINE TEST")
print("=" * 55)
print(f"Total Suggestions : {result['total_suggestions']}")
print(f"AI Powered        : {result['ai_powered']}")

print(f"\n🔴 Critical ({len(result['critical'])}):")
for s in result['critical']:
    print(f"  • {s['title']}")
    print(f"    Issue : {s['issue'][:60]}...")
    print(f"    Fix   : {s['fix'][:60]}...")

print(f"\n🟡 Improvements ({len(result['improvements'])}):")
for s in result['improvements']:
    print(f"  • {s['title']}")

print(f"\n🟢 Enhancements ({len(result['enhancements'])}):")
for s in result['enhancements']:
    print(f"  • {s['title']}")

print(f"\n✍️  Bullet Rewrites ({len(result['bullet_rewrites'])}):")
for rw in result['bullet_rewrites']:
    print(f"  Before: {rw['original'][:50]}...")
    print(f"  After : {rw['improved'][:50]}...")
    print()

print(f"\n👤 Suggested Summary:")
print(f"  {result['summary_suggestion'][:120]}...")

print("\n✅ Suggestion Engine working!")