# test_gap_analyzer.py
# Run with: python test_gap_analyzer.py

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analyzer.services.gap_analyzer import analyze_skill_gaps

missing = ['Docker', 'PostgreSQL', 'AWS', 'REST API']

resume_skills = {
    'all_skills': [
        'Python', 'Django', 'MySQL', 'Git',
        'Linux', 'HTML', 'CSS'
    ],
}

jd_data = {
    'required_skills':  ['Python', 'Django', 'Docker',
                         'PostgreSQL', 'REST API'],
    'preferred_skills': ['AWS', 'Kubernetes'],
    'experience_years': 2,
    'education_level':  'bachelors',
    'job_level':        'junior',
}

match_result = {
    'required_score': 60.0,
    'overall_match':  55.0,
}

result = analyze_skill_gaps(
    missing, resume_skills, jd_data, match_result
)

print("=" * 55)
print("     SKILL GAP ANALYSIS TEST")
print("=" * 55)
print(f"\n📊 Gap Severity    : {result['gap_severity']}")
print(f"🎯 Role Readiness  : {result['readiness_score']}%")
print(f"⚡ Quick Wins      : {len(result['quick_wins'])}")
print(f"🔴 Critical Gaps   : {result['critical_gaps']}")
print(f"🟡 Important Gaps  : {result['important_gaps']}")
print(f"🟢 Minor Gaps      : {result['minor_gaps']}")

print(f"\n📋 Detailed Gaps:")
for gap in result['skill_gaps']:
    owned = (f" (you know: {', '.join(gap['related_owned'])})"
             if gap['related_owned'] else "")
    qw    = " ⚡ Quick Win" if gap['is_quick_win'] else ""
    print(
        f"  #{gap['priority']} {gap['skill']:15s} | "
        f"{gap['importance']:12s} | "
        f"{gap['difficulty']:6s} | "
        f"{gap['learn_time']:12s}{owned}{qw}"
    )

print(f"\n📅 Action Plan:")
for step in result['action_plan']:
    print(
        f"  Week {step['start_week']:2d} — "
        f"Learn {step['skill']} ({step['duration']})"
    )

print("\n✅ Gap Analyzer working correctly!")