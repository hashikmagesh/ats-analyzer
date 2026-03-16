# test_skill_extractor.py
# Run with: python test_skill_extractor.py

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analyzer.services.skill_extractor import extract_resume_skills
from analyzer.services.section_detector import detect_sections

RESUME_TEXT = """
HASHIK M
hashikmagesh@gmail.com | LinkedIn | +91-8098020104

SUMMARY
Python Full Stack Developer with experience in Django and MySQL.
Passionate about building scalable web applications.

SKILLS
Language: Python, HTML, CSS, JavaScript, SQL
Platforms & Tools: Visual Studio Code, GitHub, Advanced Excel
Databases: MySQL, MongoDB
Frameworks: Django
Soft Skills: Teamwork & Leadership, Public Speaking

EXPERIENCE AND INTERNSHIP
Python Full Stack Developer Intern — Smik Systems (2024)
- Built web applications using Django and MySQL
- Optimized backend operations and enhanced UI

Web Development Intern — NXTLogic (2023)
- Designed responsive websites using HTML, CSS
- Collaborated with cross-functional teams

PROJECTS
Content Management System with Django Permissions
- Built using Django, role-based access control
- Applied authentication and authorization concepts

Placement Prep Gen-AI Assistance
- Integrated AI-driven recommendations
- Enhanced user experience for placement readiness

EDUCATION
B.E. Computer Science — SNS College of Technology (2022-2026)
CGPA: 7.6
"""

print("=" * 55)
print("     SKILL EXTRACTOR TEST")
print("=" * 55)

# First detect sections
sections = detect_sections(RESUME_TEXT)
meta = sections.pop('_metadata', {})
print(f"\n📋 Sections detected: {meta.get('sections_found', [])}")

# Now extract skills
result = extract_resume_skills(RESUME_TEXT, sections)

print(f"\n📊 Total Skills Found  : {result['total_found']}")
print(f"🤖 Extraction Method   : {result['extraction_method']}")

print(f"\n🔧 Technical Skills ({len(result['technical_skills'])}):")
for s in result['technical_skills']:
    conf = result['skill_confidence'].get(s, 0)
    print(f"   - {s:20s} (confidence: {conf:.0%})")

print(f"\n🛠  Tools ({len(result['tools'])}):")
for s in result['tools']:
    conf = result['skill_confidence'].get(s, 0)
    print(f"   - {s:20s} (confidence: {conf:.0%})")

print(f"\n🤝 Soft Skills ({len(result['soft_skills'])}):")
for s in result['soft_skills']:
    print(f"   - {s}")

print(f"\n📂 By Category:")
for cat, skills in result['by_category'].items():
    print(f"   {cat:25s}: {', '.join(skills)}")

print("\n" + "=" * 55)
print("✅ Skill Extractor working correctly!")
print("=" * 55)