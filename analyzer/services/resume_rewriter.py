# analyzer/services/resume_rewriter.py

import os
import re
import logging

logger = logging.getLogger(__name__)

# ── OpenAI ────────────────────────────────────────────
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = bool(os.getenv('OPENAI_API_KEY', ''))
    openai_client = (
        OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if OPENAI_AVAILABLE else None
    )
except Exception:
    OPENAI_AVAILABLE = False
    openai_client    = None

# Force disable OpenAI if key is missing or invalid
_openai_key = os.getenv('OPENAI_API_KEY', '').strip()
if not _openai_key or _openai_key.endswith('634A'):
    OPENAI_AVAILABLE = False
    openai_client    = None

# ── Gemini ────────────────────────────────────────────
import requests

GEMINI_KEY       = os.getenv('GEMINI_API_KEY', '')
GEMINI_AVAILABLE = bool(GEMINI_KEY)
GEMINI_URL       = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-2.5-flash:generateContent"
)


class ResumeRewriter:
    """
    Rewrites a resume using AI to be ATS-optimized
    for a specific job description.

    Two modes:
    1. AI Mode  — uses GPT-4o-mini or Gemini
    2. Rule Mode — fallback if no API key

    Usage:
        rewriter = ResumeRewriter(
            resume_text, sections,
            jd_data, match_result,
            gap_analysis
        )
        result = rewriter.rewrite()
    """

    def __init__(self, resume_text, sections,
                 jd_data, match_result, gap_analysis):
        self.resume_text  = resume_text
        self.sections     = sections
        self.jd_data      = jd_data
        self.match_result = match_result
        self.gap_analysis = gap_analysis

    # ─────────────────────────────────────────────────
    # MAIN METHOD
    # ─────────────────────────────────────────────────
    def rewrite(self):
        """
        Returns:
        {
            'optimized_resume': '...full rewritten text...',
            'changes_made':     [...list of changes],
            'sections_rewritten': [...],
            'ai_powered':       True/False,
            'model_used':       'gemini-1.5-flash',
            'error':            None or '...',
        }
        """
        if OPENAI_AVAILABLE or GEMINI_AVAILABLE:
            return self._ai_rewrite()
        else:
            return self._rule_rewrite()

    # ─────────────────────────────────────────────────
    # AI REWRITE
    # ─────────────────────────────────────────────────
    def _ai_rewrite(self):
        """Uses Gemini first, OpenAI as fallback."""
        prompt = self._build_rewrite_prompt()

        try:
            # ── Gemini first ──────────────────────────
            if GEMINI_AVAILABLE:
                text, model = self._call_gemini(prompt)
            elif OPENAI_AVAILABLE and openai_client:
                text, model = self._call_openai(prompt)
            else:
                return self._rule_rewrite()

            result = self._parse_rewrite_response(text)
            result['ai_powered'] = True
            result['model_used'] = model
            result['error']      = None
            return result

        except Exception as e:
            logger.error(f"AI rewrite failed: {e}")
            result          = self._rule_rewrite()
            result['error'] = str(e)
            return result

    def _build_rewrite_prompt(self):

        required     = self.jd_data.get('required_skills', [])
        missing      = self.match_result.get('missing_required', [])
        keywords     = self.jd_data.get('keywords', [])
        job_level    = self.jd_data.get('job_level', 'mid')
        job_title    = self.jd_data.get('job_title', 'Software Developer')

        resume_trimmed = self.resume_text[:1800]

        # Extract sections for explicit injection
        cert_text     = self.sections.get(
            'certifications', ''
        ).strip()
        projects_text = self.sections.get(
            'projects', ''
        ).strip()[:500]
        edu_text      = self.sections.get(
            'education', ''
        ).strip()

        return f"""You are an expert ATS resume writer.
    Your job is to FIX and REWRITE this resume completely.

    ORIGINAL RESUME:
    {resume_trimmed}

    TARGET JOB:
    Title          : {job_title}
    Level          : {job_level}
    Required Skills: {', '.join(required[:8])}
    Missing Skills : {', '.join(missing[:5])}
    Keywords       : {', '.join(keywords[:8])}

    CERTIFICATIONS TO PRESERVE:
    {cert_text if cert_text else 'Full stack development, Data Analytics'}

    EDUCATION TO PRESERVE:
    {edu_text if edu_text else 'See original resume'}

    ═══════════════════════════════════════
    FIX THESE ISSUES — MANDATORY:
    ═══════════════════════════════════════

    FIX 1 — CONTACT POSITION:
    Move contact info (email, phone, linkedin) to
    line 2, immediately after the candidate name.
    Format: name@email.com | linkedin.com/in/... | phone

    FIX 2 — SECTION ORDER:
    Output sections in EXACTLY this order:
    1. Name
    2. Contact (email | linkedin | phone)
    3. Summary
    4. Education
    5. Skills
    6. Experience and Internship
    7. Projects
    8. Certifications

    FIX 3 — EXPERIENCE PARAGRAPHS TO BULLETS:
    Convert every experience paragraph into exactly
    3 bullet points:
    - Bullet 1: What you built/did (with tech stack)
    - Bullet 2: Measurable result with a number/metric
    - Bullet 3: Teamwork or collaboration impact

    FIX 4 — WEAK VERBS:
    Replace ALL of these weak verbs:
    "Completed" → Engineered / Developed / Delivered
    "Helped"    → Collaborated / Supported
    "Did"       → Executed / Implemented
    "Used"      → Leveraged / Utilized
    "Worked on" → Built / Developed

    FIX 5 — ADD METRICS:
    Add realistic metrics to ALL experience bullets:
    - % improvement (performance, efficiency, speed)
    - Numbers (users, features, pages, team size)
    - Time saved or reduction in effort
    If no real metric exists, use "by approximately X%"

    FIX 6 — SUMMARY:
    Rewrite summary in 3 sentences:
    Sentence 1: Role + years/level + top 2 tech skills
    Sentence 2: Biggest achievement (use the 80% metric
                from AI Resume Analyzer if present)
    Sentence 3: What value you bring to target company

    FIX 7 — SKILLS FORMAT:
    Keep EXACTLY these category names:
    - Languages    : [values]
    - Frameworks   : [values]
    - Databases    : [values]
    - Tools        : [values]
    - Soft Skills  : [values]
    Add any missing required skills to correct category.

    FIX 8 — PROJECT BULLETS:
    Convert each project from paragraph to 2-3 bullets:
    - Bullet 1: What was built + tech used
    - Bullet 2: Impact or metric
    - Bullet 3: Key technical achievement (if needed)

    FIX 9 — CERTIFICATIONS:
    List certifications as clean bullets.
    NEVER write just a dash.
    Copy these exactly: {cert_text if cert_text else 'Full stack development | Data Analytics'}

    ═══════════════════════════════════════
    STRICT RULES:
    ═══════════════════════════════════════
    ✅ Plain text only — NO markdown, NO ** bold **
    ✅ Use • for ALL bullet points (never use -)
    ✅ Complete every section — never truncate
    ✅ Keep all real facts — never invent jobs
    ✅ Include ALL projects from original

    ❌ Never use markdown formatting
    ❌ Never write a lone dash - under any section
    ❌ Never skip Education section
    ❌ Never merge all skills into one bullet
    ❌ Never invent companies or qualifications
    

    ═══════════════════════════════════════
    OUTPUT FORMAT — return EXACTLY this:
    ═══════════════════════════════════════

    OPTIMIZED_RESUME_START
    [Full fixed resume here]
    OPTIMIZED_RESUME_END

    CHANGES_START
    1. Moved contact info to line 2
    2. Reordered sections (Education before Skills)
    3. Converted experience paragraphs to 3 bullets each
    4. Replaced weak verbs with strong action verbs
    5. Added metrics to all experience bullets
    6. Rewrote summary for target role
    7. [Any other changes made]
    CHANGES_END"""

    def _post_process(self, text):
        """
        Programmatically fixes common issues in AI output.
        Runs after AI rewrite as a safety net.
        """
        lines   = text.split('\n')
        fixed   = []
        i       = 0

        while i < len(lines):
            line = lines[i]

            # ── Fix 1: Remove lone dashes ──────────────
            # A line that is just "- " or "-" = empty section
            if line.strip() in ['-', '- ', '–', '—']:
                i += 1
                continue

            # ── Fix 2: Normalize bullets ───────────────
            # Convert all - bullets to • bullets
            stripped = line.lstrip()
            indent   = len(line) - len(stripped)
            if stripped.startswith('- ') and len(stripped) > 3:
                line = ' ' * indent + '• ' + stripped[2:]

            # ── Fix 3: Remove markdown bold ───────────
            line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            line = re.sub(r'\*(.*?)\*',     r'\1', line)

            # ── Fix 4: Fix contact line separators ─────
            if '@' in line and ('http' in line or
                                re.search(r'\d{8,}', line)):
                # Replace " - " with " | " in contact lines
                line = re.sub(r'\s*-\s*', ' | ', line)
                line = line.lstrip('|-• ').strip()
                line = line.replace('||', '|').strip('|').strip()

            # ── Fix 5: Remove ALL CAPS skill values ────
            # Only fix lines that look like skill lines
            if ':' in line and len(line) < 100:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    label  = parts[0].strip()
                    values = parts[1].strip()
                    # If values are ALL CAPS, convert to Title/lower
                    if (values == values.upper() and
                            len(values) > 3 and
                            values.replace(',', '')
                                .replace(' ', '')
                                .isalpha()):
                        # Keep label, fix values case
                        values = ', '.join(
                            v.strip().title()
                            for v in values.split(',')
                        )
                        line = f"{label}: {values}"

            fixed.append(line)
            i += 1

        return '\n'.join(fixed)


    def _ensure_certifications(self, text):
        """
        Safety check — if certifications section exists
        but is empty, inject the original cert content.
        """
        cert_text = self.sections.get('certifications', '').strip()
        if not cert_text:
            cert_text = 'Full stack development\nData Analytics'

        lines  = text.split('\n')
        result = []
        i      = 0

        while i < len(lines):
            result.append(lines[i])

            # Found certifications header
            if 'CERTIFICATION' in lines[i].upper():
                # Check if next non-empty line is just a dash
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1

                if j < len(lines) and lines[j].strip() in [
                    '-', '–', '—', '- '
                ]:
                    # Replace the dash with real content
                    result.append('')
                    for cert in cert_text.split('\n'):
                        if cert.strip():
                            result.append(f'• {cert.strip()}')
                    i = j + 1  # Skip the dash line
                    continue

            i += 1

        return '\n'.join(result)

    def _call_openai(self, prompt):
        """Calls GPT-4o-mini."""
        response = openai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are an expert ATS resume writer. '
                        'You rewrite resumes to be optimized for '
                        'specific job descriptions without '
                        'fabricating any information.'
                    ),
                },
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=2000,
            temperature=0.4,
        )
        return (
            response.choices[0].message.content,
            'gpt-4o-mini'
        )

    def _call_gemini(self, prompt):
        """Calls Gemini via direct REST API."""
        try:
            url     = f"{GEMINI_URL}?key={GEMINI_KEY}"
            headers = {"Content-Type": "application/json"}
            data    = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "maxOutputTokens": 8192,
                    "temperature": 0.4,
                    "stopSequences":   [],
                }
            }

            response = requests.post(
                url, headers=headers, json=data, timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                text   = result["candidates"][0]["content"]["parts"][0]["text"]
                return text, 'gemini-2.5-flash'
            else:
                logger.error(
                    f"Gemini error: {response.status_code}"
                )
                raise Exception(
                    f"Gemini {response.status_code}: "
                    f"{response.text[:200]}"
                )

        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            raise

    def _parse_rewrite_response(self, text):
        """
        Parses the structured AI response.
        Extracts the optimized resume and change list.
        """
        optimized = ''
        changes   = []

        # ── Extract optimized resume ───────────────────
        resume_match = re.search(
            r'OPTIMIZED_RESUME_START\s*(.*?)\s*OPTIMIZED_RESUME_END',
            text,
            re.DOTALL
        )
        if resume_match:
            optimized = resume_match.group(1).strip()
        else:
            # Fallback: use everything before CHANGES_START
            parts = text.split('CHANGES_START')
            optimized = parts[0].strip()
            # Clean up any leftover markers
            optimized = re.sub(
                r'OPTIMIZED_RESUME_START|OPTIMIZED_RESUME_END',
                '',
                optimized
            ).strip()

            optimized = self._strip_markdown(optimized)
            optimized = self._post_process(optimized)          # ← ADD
            optimized = self._ensure_certifications(optimized) # ← ADD

        # ── Extract changes list ───────────────────────
        changes_match = re.search(
            r'CHANGES_START\s*(.*?)\s*CHANGES_END',
            text,
            re.DOTALL
        )
        if changes_match:
            raw_changes = changes_match.group(1).strip()
            for line in raw_changes.split('\n'):
                line = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                if line and len(line) > 10:
                    changes.append(line)

        # Fallback changes if none parsed
        if not changes:
            changes = [
                'Strengthened action verbs throughout',
                'Added metrics to experience bullets',
                'Incorporated target job keywords',
                'Improved professional summary',
                'Organized skills by category',
            ]

        return {
            'optimized_resume':   optimized,
            'changes_made':       changes[:8],
            'sections_rewritten': self._detect_rewritten(
                optimized
            ),
            
        }

    def _strip_markdown(self, text):
        """
        Removes markdown formatting that Gemini adds.
        Cleans ** bold **, * bullets, # headers etc.
        """
        # Remove bold/italic markers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*',     r'\1', text)  # *italic*

        # Remove any remaining stray asterisks at line ends
        text = re.sub(r'\*+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*+\s', ' ',  text)

        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Clean up extra spaces
        text = re.sub(r'  +', ' ', text)

        return text.strip()

    def _detect_rewritten(self, optimized_text):
        """Detects which sections were rewritten."""
        rewritten = []
        checks    = {
            'Summary':    ['summary', 'objective', 'profile'],
            'Experience': ['experience', 'work history',
                           'internship'],
            'Skills':     ['skills', 'technical skills',
                           'technologies'],
            'Education':  ['education', 'academic'],
        }
        lower = optimized_text.lower()
        for section, keywords in checks.items():
            if any(kw in lower for kw in keywords):
                rewritten.append(section)
        return rewritten

    # ─────────────────────────────────────────────────
    # RULE-BASED REWRITE (fallback, no API needed)
    # ─────────────────────────────────────────────────
    def _rule_rewrite(self):
        """
        Rewrites the resume using rules only.
        Works without any API key.
        """
        lines    = self.resume_text.split('\n')
        rewritten = []
        changes   = []

        WEAK_MAP = {
            r'\bworked on\b':         'Developed',
            r'\bhelped with\b':       'Collaborated on',
            r'\bassisted with\b':     'Supported',
            r'\bwas responsible for\b': 'Led',
            r'\bresponsible for\b':   'Managed',
            r'\bused\b':              'Leveraged',
            r'\bdid\b':               'Executed',
            r'\bmade\b':              'Designed',
            r'\bworked with\b':       'Collaborated with',
            r'\bhelped\b':            'Assisted',
            r'\binvolved in\b':       'Contributed to',
        }

        verb_fixed   = 0
        metric_added = 0

        for line in lines:
            new_line = line

            # Fix weak verbs in bullet points
            stripped = line.strip()
            is_bullet = (
                stripped.startswith('-') or
                stripped.startswith('•') or
                (stripped and stripped[0].isupper()
                 and len(stripped) > 15)
            )

            if is_bullet:
                for pattern, replacement in WEAK_MAP.items():
                    if re.search(pattern, new_line,
                                 re.IGNORECASE):
                        new_line = re.sub(
                            pattern, replacement,
                            new_line, count=1,
                            flags=re.IGNORECASE
                        )
                        verb_fixed += 1
                        break

                # Add metric if no numbers and is experience bullet
                exp_text = self.sections.get('experience', '').lower()
                is_exp_bullet = (
                    is_bullet and
                    any(word in new_line.lower() for word in
                        ['develop', 'build', 'engineer', 'design',
                        'implement', 'optimiz', 'collaborat',
                        'deliver', 'manag', 'creat'])
                )
                if (is_exp_bullet and
                        not re.search(r'\d', new_line) and
                        len(new_line.strip()) > 20 and
                        metric_added < 3):
                    new_line = new_line.rstrip() + \
                               ', improving efficiency by ~20%'
                    metric_added += 1

            rewritten.append(new_line)

        # Add missing skills note at end of skills section
        # missing = self.match_result.get('missing_required', [])
        # if missing:
        #     final_lines = []
        #     in_skills   = False
        #     added       = False
        #     for line in rewritten:
        #         final_lines.append(line)
        #         lower = line.lower()
        #         if 'skill' in lower and len(line) < 30:
        #             in_skills = True
        #         if (in_skills and not added and
        #                 len(line.strip()) > 20):
        #             # Add missing skills note
        #             final_lines.append(
        #                 f'[Consider adding: '
        #                 f'{", ".join(missing[:3])}]'
        #             )
        #             added = True
        #     rewritten = final_lines

        if verb_fixed:
            changes.append(
                f'Replaced {verb_fixed} weak verbs with '
                f'strong action verbs'
            )
        if metric_added:
            changes.append(
                f'Added approximate metrics to '
                f'{metric_added} bullet points'
            )
        # if missing:
        #     changes.append(
        #         f'Flagged {len(missing)} missing required '
        #         f'skills to add: '
        #         f'{", ".join(missing[:3])}'
        #     )
        changes.append(
            'Note: Add your API key for full AI rewriting '
            'with deep optimization'
        )

        return {
            'optimized_resume':   '\n'.join(rewritten),
            'changes_made':       changes,
            'sections_rewritten': ['Experience', 'Skills'],
            'ai_powered':         False,
            'model_used':         'Rule-based (no API key)',
            'error':              None,
        }


# ─────────────────────────────────────────────────────
# STANDALONE HELPER
# ─────────────────────────────────────────────────────
def rewrite_resume(resume_text, sections, jd_data,
                   match_result, gap_analysis):
    """
    Shortcut helper.

    Usage:
        from analyzer.services.resume_rewriter import rewrite_resume
        result = rewrite_resume(...)
    """
    rewriter = ResumeRewriter(
        resume_text, sections, jd_data,
        match_result, gap_analysis
    )
    return rewriter.rewrite()