# analyzer/services/section_detector.py

import re
import logging

logger = logging.getLogger(__name__)


class SectionDetector:
    """
    Detects and extracts sections from resume text.

    How it works:
    1. We define keywords for each section header
       (e.g. "EXPERIENCE", "WORK HISTORY", "EMPLOYMENT")
    2. We scan the text line by line
    3. When we find a header keyword, we start collecting
       text under that section
    4. When we find the NEXT header, we stop the previous section

    Usage:
        detector = SectionDetector(resume_text)
        sections = detector.detect()
        print(sections['skills'])
        print(sections['experience'])
    """

    # ─────────────────────────────────────────────────
    # SECTION HEADER KEYWORDS
    # Each key is our internal section name.
    # The list contains all possible header variations
    # we might see in real resumes.
    # ─────────────────────────────────────────────────
    SECTION_HEADERS = {

        'summary': [
            'summary', 'professional summary', 'career summary',
            'objective', 'career objective', 'profile',
            'professional profile', 'about me', 'overview',
            'personal statement', 'introduction', 'bio',
        ],

        'experience': [
            'experience', 'work experience', 'professional experience',
            'employment', 'employment history', 'work history',
            'career history', 'job history', 'positions held',
            'professional background', 'relevant experience',
            'internship', 'internships',
            'experience and internship',       # ← ADD THIS
            'experience & internship',         # ← ADD THIS
            'internship and experience',
        ],

        'education': [
            'education', 'educational background', 'academic background',
            'qualifications', 'academic qualifications',
            'degrees', 'academic history', 'schooling',
            'educational qualifications', 'university', 'college',
        ],

        'skills': [
            'skills', 'technical skills', 'core skills',
            'key skills', 'competencies', 'core competencies',
            'technologies', 'tech stack', 'tools',
            'tools and technologies', 'programming languages',
            'languages', 'expertise', 'proficiencies',
            'abilities', 'technical expertise',
        ],

        'projects': [
            'projects', 'personal projects', 'academic projects',
            'key projects', 'notable projects', 'portfolio',
            'side projects', 'open source', 'github projects',
            'project experience', 'major projects',
        ],

        'certifications': [
            'certifications', 'certificates','certificate', 'certification',
            'professional certifications', 'licenses',
            'accreditations', 'credentials', 'courses',
            'training', 'professional development',
        ],

        'achievements': [
            'achievements', 'accomplishments', 'awards',
            'honors', 'recognition', 'accolades',
            'achievements and awards',
            'extracurricular', 'extracurricular activities',   # ← ADD THIS
            'extra curricular activities',                     # ← ADD THIS
            'activities',   
        ],

        'contact': [
            'contact', 'contact information', 'contact details',
            'personal information', 'personal details',
            'personal data',
        ],
    }

    def __init__(self, resume_text):
        self.resume_text = resume_text
        self.lines = resume_text.split('\n')

    # ─────────────────────────────────────────────────
    # MAIN METHOD
    # ─────────────────────────────────────────────────
    def detect(self):
        """
        Main entry point. Detects all sections.

        Returns:
        {
            'summary':          'text...',
            'experience':       'text...',
            'education':        'text...',
            'skills':           'text...',
            'projects':         'text...',
            'certifications':   'text...',
            'achievements':     'text...',
            'contact':          'text...',
            'header':           'text...',  ← name/contact at top
            'other':            'text...',  ← unmatched sections
            '_metadata': {
                'sections_found':   [...],
                'total_lines':      120,
                'detection_method': 'keyword'
            }
        }
        """
        # Step 1 — Find where each section starts
        section_boundaries = self._find_section_boundaries()

        # Step 2 — Extract text between boundaries
        sections = self._extract_section_text(section_boundaries)

        # Step 3 — Extract the resume header (name, contact)
        sections['header'] = self._extract_header()

        # Step 4 — Add metadata
        sections['_metadata'] = {
            'sections_found': [
                k for k, v in sections.items()
                if v and k != '_metadata'
            ],
            'total_lines': len(self.lines),
            'detection_method': 'keyword',
        }

        logger.info(
            f"Sections detected: "
            f"{sections['_metadata']['sections_found']}"
        )

        return sections

    # ─────────────────────────────────────────────────
    # STEP 1: FIND SECTION BOUNDARIES
    # ─────────────────────────────────────────────────
    def _find_section_boundaries(self):
        """
        Scans every line to find section headers.

        Returns a list of tuples:
        [
            (line_index, section_name, original_header_text),
            (5,  'summary',    'PROFESSIONAL SUMMARY'),
            (18, 'experience', 'WORK EXPERIENCE'),
            (45, 'education',  'EDUCATION'),
            ...
        ]
        """
        boundaries = []

        for line_idx, line in enumerate(self.lines):
            # Clean the line for comparison
            clean_line = line.strip().lower()

            # Skip empty lines
            if not clean_line:
                continue

            # Skip very long lines — headers are usually short
            # (A line with 100+ chars is probably content, not a header)
            if len(clean_line) > 80:
                continue

            # Check if this line matches any section header
            matched_section = self._match_header(clean_line)

            if matched_section:
                boundaries.append((
                    line_idx,
                    matched_section,
                    line.strip()  # Original text
                ))

        return boundaries

    # ─────────────────────────────────────────────────
    # STEP 2: EXTRACT TEXT BETWEEN BOUNDARIES
    # ─────────────────────────────────────────────────
    def _extract_section_text(self, boundaries):
        """
        Given the boundaries, extract the text that
        belongs to each section.

        If sections = [(5, 'summary'), (18, 'experience'), (45, 'education')]
        Then:
          summary    = lines 6 to 17
          experience = lines 19 to 44
          education  = lines 46 to end
        """
        # Start with empty sections
        sections = {key: '' for key in self.SECTION_HEADERS.keys()}
        sections['other'] = ''

        if not boundaries:
            # No sections found — put everything in 'other'
            sections['other'] = self.resume_text
            return sections

        for i, (line_idx, section_name, header_text) in enumerate(boundaries):

            # Content starts on the line AFTER the header
            content_start = line_idx + 1

            # Content ends where the NEXT section starts
            if i + 1 < len(boundaries):
                content_end = boundaries[i + 1][0]
            else:
                content_end = len(self.lines)  # Last section goes to end

            # Extract lines for this section
            section_lines = self.lines[content_start:content_end]

            # Join and clean
            section_text = '\n'.join(section_lines).strip()

            # Handle duplicate sections (e.g. two 'experience' headers)
            # by appending instead of overwriting
            if sections.get(section_name):
                sections[section_name] += '\n\n' + section_text
            else:
                sections[section_name] = section_text

        return sections

    # ─────────────────────────────────────────────────
    # STEP 3: EXTRACT HEADER (Name + Contact Info)
    # ─────────────────────────────────────────────────
    def _extract_header(self):
        """
        Extracts the top part of the resume — typically
        the candidate's name, email, phone, LinkedIn.

        Strategy: Take lines from the top until we hit
        the first real section header.
        """
        header_lines = []

        for line in self.lines[:15]:  # Only check first 15 lines
            clean = line.strip().lower()

            if not clean:
                continue

            # Stop if we hit a section header
            if self._match_header(clean):
                break

            header_lines.append(line.strip())

        return '\n'.join(header_lines)

    # ─────────────────────────────────────────────────
    # HEADER MATCHING LOGIC
    # ─────────────────────────────────────────────────
    def _match_header(self, line):

        """
        Checks if a line matches any known section header.
        Also handles two headers merged on the same line
        (happens with two-column PDF layouts).
        """
        line = line.strip().lower()
        line_clean = re.sub(r'[:\-–—|•*#]+', '', line).strip()

        # ── NEW: Handle two merged headers on one line ──
        # e.g. "certification extracurricular activities"
        # We check if the line STARTS WITH a known keyword
        for section_name, keywords in self.SECTION_HEADERS.items():
            for keyword in keywords:
                if line_clean.startswith(keyword):
                    return section_name

        # ── Original matching ───────────────────────────
        for section_name, keywords in self.SECTION_HEADERS.items():
            for keyword in keywords:
                # Exact match
                if line_clean == keyword:
                    return section_name

                # Keyword contained in short line
                if keyword in line_clean and len(line_clean) < 50:
                    return section_name

        return None

    # ─────────────────────────────────────────────────
    # UTILITY: GET SPECIFIC SECTION
    # ─────────────────────────────────────────────────
    def get_section(self, section_name):
        """
        Quick way to get just one section.

        Usage:
            detector = SectionDetector(text)
            skills_text = detector.get_section('skills')
        """
        sections = self.detect()
        return sections.get(section_name, '')

    # ─────────────────────────────────────────────────
    # UTILITY: PRETTY PRINT SECTIONS (for debugging)
    # ─────────────────────────────────────────────────
    def print_sections(self):
        """Prints a readable summary of detected sections."""
        sections = self.detect()

        print("\n" + "=" * 55)
        print("       RESUME SECTION DETECTION RESULTS")
        print("=" * 55)

        for name, content in sections.items():
            if name == '_metadata':
                continue
            if content:
                preview = content[:80].replace('\n', ' ')
                print(f"\n📌 [{name.upper()}]")
                print(f"   Length  : {len(content)} chars")
                print(f"   Preview : {preview}...")
            else:
                print(f"\n   [{name.upper()}] — not found")

        meta = sections.get('_metadata', {})
        print(f"\n{'=' * 55}")
        print(f"  Sections Found : "
              f"{meta.get('sections_found', [])}")
        print(f"  Total Lines    : {meta.get('total_lines', 0)}")
        print("=" * 55 + "\n")


# ─────────────────────────────────────────────────────
# STANDALONE HELPER FUNCTION
# ─────────────────────────────────────────────────────
def detect_sections(resume_text):
    """
    Simple helper — shortcut for using SectionDetector.

    Usage:
        from analyzer.services.section_detector import detect_sections
        sections = detect_sections(resume_text)
    """
    detector = SectionDetector(resume_text)
    return detector.detect()