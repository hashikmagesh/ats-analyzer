# test_exporter.py
# Run with: python test_exporter.py

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analyzer.services.resume_exporter import (
    export_as_pdf, export_as_docx, extract_candidate_name
)

resume_text = """HASHIK M
hashikmagesh@gmail.com | +91-8098020104 | linkedin.com/in/hashik

SUMMARY
Results-driven Junior Developer with experience in Python and Django.
Passionate about building scalable web applications.

EXPERIENCE AND INTERNSHIP
Python Full Stack Developer — Smik Systems (2024-Present)
- Engineered Django web applications improving response time by 30%
- Optimized 15 MySQL queries reducing page load by 40%
- Collaborated with cross-functional teams to deliver features

Web Development Intern — NXTLogic (2023-2024)
- Developed 5 responsive websites using HTML, CSS, JavaScript
- Improved website performance by optimizing assets by 25%

SKILLS
Languages : Python, JavaScript, HTML, CSS
Frameworks: Django, React
Databases : MySQL, MongoDB
Tools     : Git, Docker (beginner), REST APIs

EDUCATION
B.E. Computer Science — SNS College of Technology
2022-2026 | CGPA: 7.6
"""

print("Testing Resume Exporter...")
print("=" * 45)

# Test name extraction
name = extract_candidate_name(resume_text)
print(f"Candidate Name : {name}")

# Test PDF
print("\nGenerating PDF...")
try:
    pdf = export_as_pdf(resume_text, name)
    with open('test_output.pdf', 'wb') as f:
        f.write(pdf)
    print(f"✅ PDF generated: {len(pdf):,} bytes")
    print("   Saved as: test_output.pdf")
except Exception as e:
    print(f"❌ PDF failed: {e}")

# Test DOCX
print("\nGenerating DOCX...")
try:
    docx = export_as_docx(resume_text, name)
    with open('test_output.docx', 'wb') as f:
        f.write(docx)
    print(f"✅ DOCX generated: {len(docx):,} bytes")
    print("   Saved as: test_output.docx")
except Exception as e:
    print(f"❌ DOCX failed: {e}")

print("\n✅ Exporter test complete!")
print("Open test_output.pdf and test_output.docx to verify.")