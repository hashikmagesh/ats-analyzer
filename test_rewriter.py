# test_rewriter.py
# Run with: python test_rewriter.py

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analyzer.services.resume_rewriter import rewrite_resume

resume_text = """
HASHIK M
hashikmagesh@gmail.com | +91-8098020104

SUMMARY
Python developer with internship experience.

EXPERIENCE AND INTERNSHIP
Python Full Stack Developer — Smik Systems (2024-Present)
- Worked on Django web applications
- Helped with MySQL database optimization
- Used Git for version control and collaboration

Web Development Intern — NXTLogic (2023-2024)
- Did HTML and CSS work for 5 client websites
- Assisted with making responsive designs

SKILLS
Python, Django, MySQL, MongoDB, HTML, CSS, JavaScript, Git

EDUCATION
B.E. Computer Science — SNS College of Technology
2022-2026 | CGPA: 7.6
"""

sections = {
    'summary':    'Python developer with internship experience.',
    'experience': (
        'Python Full Stack Developer — Smik Systems\n'
        '- Worked on Django web applications\n'
        '- Helped with MySQL database optimization'
    ),
    'skills':     'Python, Django, MySQL, HTML, CSS, Git',
    'education':  'B.E. Computer Science 2022-2026',
}

jd_data = {
    'required_skills':  ['Python', 'Django', 'REST API',
                         'PostgreSQL', 'Git'],
    'preferred_skills': ['Docker', 'AWS'],
    'job_level':        'junior',
    'experience_years': 1,
    'keywords':         ['backend', 'scalable', 'agile',
                         'api', 'performance'],
}

match_result = {
    'matched_required': ['Python', 'Django', 'Git'],
    'missing_required': ['REST API', 'PostgreSQL'],
    'overall_match':    60.0,
}

gap_analysis = {
    'critical_gaps': ['REST API', 'PostgreSQL'],
    'skill_gaps':    [],
}

result = rewrite_resume(
    resume_text, sections, jd_data,
    match_result, gap_analysis
)

print("=" * 55)
print("     RESUME REWRITER TEST")
print("=" * 55)
print(f"AI Powered  : {result['ai_powered']}")
print(f"Model Used  : {result['model_used']}")
print(f"Error       : {result.get('error', 'None')}")
print(f"\n📝 Changes Made:")
for c in result['changes_made']:
    print(f"  ✓ {c}")

print(f"\n✨ Optimized Resume Preview (first 400 chars):")
print("-" * 50)
print(result['optimized_resume'][:400])
print("-" * 50)
print("\n✅ Rewriter working!")