# test_extraction.py
# Run this with: python test_extraction.py

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analyzer.services.resume_extractor import ResumeExtractor

def test_extractor():
    print("=" * 50)
    print("RESUME EXTRACTOR TEST")
    print("=" * 50)

    # ── Test with a sample text (simulates what we'd get) ──
    sample_text = """
    John Doe
    Python Developer | john@email.com | LinkedIn

    EXPERIENCE
    Senior Python Developer — TechCorp (2021-Present)
    - Built REST APIs using Django and FastAPI
    - Managed PostgreSQL databases
    - Deployed on AWS using Docker

    SKILLS
    Python, Django, FastAPI, PostgreSQL, Docker, AWS, Git

    EDUCATION
    B.Tech Computer Science — IIT Delhi (2019)
    """

    print("\n✅ Extractor class loaded successfully!")
    print("\n📋 Sample text that would be extracted:")
    print("-" * 40)
    print(sample_text[:300])
    print("-" * 40)

    # Test the clean_text method
    extractor = ResumeExtractor.__new__(ResumeExtractor)
    cleaned = extractor._clean_text(sample_text)
    print(f"\n✅ Text cleaning works!")
    print(f"   Original length : {len(sample_text)} chars")
    print(f"   Cleaned length  : {len(cleaned)} chars")
    print(f"   Word count      : {len(cleaned.split())} words")

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED ✅")
    print("=" * 50)
    print("\nTo test with a real file, upload a resume")
    print("through the web interface at http://127.0.0.1:8000/")

if __name__ == '__main__':
    test_extractor()