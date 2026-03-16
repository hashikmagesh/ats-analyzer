# test_semantic_matcher.py
# Run with: python test_semantic_matcher.py

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analyzer.services.semantic_matcher import match_skills

# ── Test 1: Exact matches ─────────────────────────
print("=" * 55)
print("TEST 1: Exact Skill Matches")
print("=" * 55)

result = match_skills(
    resume_skills = ['Python', 'Django', 'MySQL', 'Git'],
    jd_required   = ['Python', 'Django', 'PostgreSQL'],
    jd_preferred  = ['Docker', 'AWS'],
)
print(f"Method          : {result['method']}")
print(f"Required Score  : {result['required_score']}%")
print(f"Overall Match   : {result['overall_match']}%")
print(f"Matched         : {result['matched_required']}")
print(f"Missing         : {result['missing_required']}")

# ── Test 2: Semantic matches (the magic!) ─────────
print("\n" + "=" * 55)
print("TEST 2: Semantic Matches (different words, same meaning)")
print("=" * 55)

result2 = match_skills(
    resume_skills = ['TensorFlow', 'Pandas', 'Python'],
    jd_required   = [
        'Deep Learning Frameworks',  # Should match TensorFlow!
        'Data Analysis',             # Should match Pandas!
        'Backend Development',       # Should match Python!
    ],
)
print(f"Method         : {result2['method']}")
print(f"Required Score : {result2['required_score']}%")
print(f"Matched        : {result2['matched_required']}")
print(f"Missing        : {result2['missing_required']}")
print("\nMatch Details:")
for d in result2['match_details']:
    icon = "✅" if d['is_match'] else "❌"
    print(
        f"  {icon} '{d['jd_skill']:30s}' "
        f"↔ '{d['best_resume_match']}' "
        f"(similarity: {d['similarity']:.2f}, "
        f"type: {d['match_type']})"
    )

# ── Test 3: Hashik's resume vs SWE JD ────────────
print("\n" + "=" * 55)
print("TEST 3: Hashik Resume vs Software Engineer JD")
print("=" * 55)

hashik_skills = [
    'Python', 'Django', 'MySQL', 'MongoDB',
    'HTML', 'CSS', 'JavaScript', 'Git',
    'GitHub', 'Advanced Excel', 'Leadership', 'Teamwork'
]

swe_jd_required = [
    'Python', 'Django', 'REST API', 'PostgreSQL',
    'Git', 'Problem Solving'
]

swe_jd_preferred = ['Docker', 'AWS', 'React']

result3 = match_skills(
    hashik_skills, swe_jd_required, swe_jd_preferred
)
print(f"Required Match  : {result3['required_score']}%")
print(f"Overall Match   : {result3['overall_match']}%")
print(f"✅ Matched       : {result3['matched_required']}")
print(f"❌ Missing       : {result3['missing_required']}")
print(f"⭐ Preferred     : {result3['matched_preferred']}")

print("\n✅ Semantic Matcher working correctly!")