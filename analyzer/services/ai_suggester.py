# analyzer/services/ai_suggester.py

import re
import os
import requests
import logging

logger = logging.getLogger(__name__)

# ── Try to import OpenAI ──────────────────────────────
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = bool(os.getenv('OPENAI_API_KEY', ''))
    if OPENAI_AVAILABLE:
        openai_client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        logger.info("OpenAI client initialized")
    else:
        openai_client = None
        logger.warning("OPENAI_API_KEY not set")
except Exception as e:
    OPENAI_AVAILABLE = False
    openai_client    = None
    logger.warning(f"OpenAI not available: {e}")

# Force disable OpenAI if key is missing or invalid
_openai_key = os.getenv('OPENAI_API_KEY', '').strip()
if not _openai_key or _openai_key.endswith('634A'):
    OPENAI_AVAILABLE = False
    openai_client    = None

# ── Try to import Gemini ──────────────────────────────



GEMINI_KEY       = os.getenv('GEMINI_API_KEY', '')
GEMINI_AVAILABLE = bool(GEMINI_KEY)
GEMINI_URL       = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-2.5-flash:generateContent"
)


class AISuggester:
    """
    Generates AI-powered resume improvement suggestions.

    Works in two modes:
    1. AI Mode (OpenAI/Gemini): Deep, contextual suggestions
       using large language models.

    2. Rule-based Mode (fallback): Smart pattern matching
       that still gives excellent suggestions without API.

    Usage:
        suggester = AISuggester(
            resume_text, sections, resume_skills,
            jd_data, match_result, ats_score
        )
        result = suggester.generate()
    """

    # ── Weak action verbs to replace ──────────────────
    WEAK_VERBS = [
        'worked', 'helped', 'assisted', 'did', 'made',
        'used', 'handled', 'was responsible', 'responsible for',
        'involved in', 'participated', 'contributed to',
        'helped with', 'worked with', 'worked on',
    ]

    # ── Strong action verbs to suggest ───────────────
    STRONG_VERBS = {
        'built':       ['developed', 'engineered', 'created'],
        'improved':    ['optimized', 'enhanced', 'streamlined'],
        'managed':     ['led', 'directed', 'oversaw'],
        'helped':      ['collaborated', 'partnered', 'supported'],
        'worked on':   ['developed', 'implemented', 'delivered'],
        'used':        ['leveraged', 'utilized', 'applied'],
        'made':        ['designed', 'architected', 'produced'],
        'did':         ['executed', 'performed', 'achieved'],
    }

    def __init__(self, resume_text, sections,
                 resume_skills, jd_data,
                 match_result, ats_score):
        self.resume_text   = resume_text
        self.sections      = sections
        self.resume_skills = resume_skills
        self.jd_data       = jd_data
        self.match_result  = match_result
        self.ats_score     = ats_score

    # ─────────────────────────────────────────────────
    # MAIN METHOD
    # ─────────────────────────────────────────────────
    def generate(self):
        """
        Generates all improvement suggestions.

        Returns:
        {
            'critical':     [...must-fix suggestions],
            'improvements': [...should-fix suggestions],
            'enhancements': [...nice-to-fix suggestions],
            'bullet_rewrites': [...rewritten bullet examples],
            'summary_suggestion': '...',
            'keyword_suggestions': [...],
            'total_suggestions': 12,
            'ai_powered': True/False,
        }
        """
        # ── Rule-based suggestions (always runs) ──────
        rule_suggestions = self._rule_based_suggestions()

        # ── AI suggestions (if API available) ─────────
        ai_result = {}
        if OPENAI_AVAILABLE or GEMINI_AVAILABLE:
            try:
                ai_result = self._ai_suggestions()
                logger.info("AI suggestions generated")
            except Exception as e:
                logger.warning(f"AI suggestion failed: {e}")
                ai_result = {}

        # ── Merge results ─────────────────────────────
        result = self._merge_suggestions(
            rule_suggestions, ai_result
        )

        return result

    # ─────────────────────────────────────────────────
    # RULE-BASED SUGGESTIONS
    # ─────────────────────────────────────────────────
    def _rule_based_suggestions(self):
        """
        Analyzes resume using rules and patterns.
        Always runs — does not need API keys.
        """
        critical     = []
        improvements = []
        enhancements = []
        rewrites     = []

        exp_text = self.sections.get('experience', '')
        sum_text = self.sections.get('summary', '')
        ski_text = self.sections.get('skills', '')

        # ── Check 1: Missing critical sections ────────
        if not sum_text:
            critical.append({
                'type':    'missing_section',
                'title':   'Add a Professional Summary',
                'issue':   'Your resume has no summary section. '
                           'ATS systems and recruiters look for '
                           'this first.',
                'fix':     'Add a 2-3 sentence summary at the '
                           'top that mentions your role, years of '
                           'experience, and top 2-3 skills.',
                'example': (
                    f'Example: "Results-driven '
                    f'{self.jd_data.get("job_level", "Software").title()} '
                    f'Developer with experience in '
                    f'{", ".join(self.resume_skills.get("technical_skills", ["Python"])[:3])}. '
                    f'Passionate about building scalable solutions '
                    f'and solving real-world problems."'
                ),
            })

        if not exp_text:
            critical.append({
                'type':  'missing_section',
                'title': 'Add Experience Section',
                'issue': 'No experience section detected.',
                'fix':   'Add an Experience or Internship section '
                         'with your work history, even if it is '
                         'just internships or projects.',
                'example': '',
            })

        # ── Check 2: Weak action verbs ─────────────────
        if exp_text:
            found_weak = []
            exp_lower  = exp_text.lower()
            for verb in self.WEAK_VERBS:
                if re.search(r'\b' + verb + r'\b', exp_lower):
                    found_weak.append(verb)

            if found_weak:
                alternatives = []
                for verb in found_weak[:3]:
                    strong = self.STRONG_VERBS.get(
                        verb,
                        ['developed', 'implemented', 'delivered']
                    )
                    alternatives.append(
                        f'"{verb}" → "{strong[0]}"'
                    )

                improvements.append({
                    'type':    'weak_verbs',
                    'title':   'Replace Weak Action Verbs',
                    'issue':   f'Found weak verbs: '
                               f'{", ".join(found_weak[:3])}. '
                               f'These reduce ATS impact.',
                    'fix':     'Start every bullet point with a '
                               'strong action verb.',
                    'example': 'Replacements: ' +
                               ' | '.join(alternatives),
                })

        # ── Check 3: Missing quantification ───────────
        if exp_text:
            numbers = re.findall(r'\d+[%\+]?', exp_text)
            if len(numbers) < 2:
                critical.append({
                    'type':    'no_quantification',
                    'title':   'Add Numbers & Metrics',
                    'issue':   'Your experience bullets have no '
                               'measurable results. ATS and '
                               'recruiters love numbers.',
                    'fix':     'Add metrics to at least 3 bullets. '
                               'Think: How many? How much? '
                               'How fast? What % improvement?',
                    'example': (
                        'Before: "Optimized database queries"\n'
                        'After:  "Optimized 15 database queries, '
                        'reducing page load time by 40%"'
                    ),
                })

        # ── Check 4: Missing JD keywords ──────────────
        missing_keywords = []
        jd_keywords      = self.jd_data.get('keywords', [])
        resume_lower     = self.resume_text.lower()

        for kw in jd_keywords[:10]:
            if kw not in resume_lower:
                missing_keywords.append(kw)

        if missing_keywords:
            improvements.append({
                'type':    'missing_keywords',
                'title':   'Add Missing JD Keywords',
                'issue':   f'These words appear in the job '
                           f'description but not in your resume: '
                           f'{", ".join(missing_keywords[:5])}',
                'fix':     'Naturally incorporate these keywords '
                           'into your summary, skills, or '
                           'experience bullets.',
                'example': f'Add to summary or skills: '
                           f'{", ".join(missing_keywords[:3])}',
            })

        # ── Check 5: Missing skills from JD ───────────
        missing_skills = self.match_result.get(
            'missing_required', []
        )
        if missing_skills:
            top_missing = missing_skills[:4]
            improvements.append({
                'type':    'missing_skills',
                'title':   f'Add {len(missing_skills)} Missing Skills',
                'issue':   f'These required skills are not on '
                           f'your resume: '
                           f'{", ".join(top_missing)}',
                'fix':     'If you have basic knowledge of any '
                           'of these, add them to your skills '
                           'section. Even beginner-level counts.',
                'example': f'Add to Skills section: '
                           f'{", ".join(top_missing[:2])} '
                           f'(beginner)',
            })

        # ── Check 6: Resume length ─────────────────────
        word_count = len(self.resume_text.split())
        if word_count < 250:
            critical.append({
                'type':    'too_short',
                'title':   'Resume is Too Short',
                'issue':   f'Your resume has only {word_count} '
                           f'words. ATS systems prefer 400-600 '
                           f'words for experienced candidates.',
                'fix':     'Expand each experience bullet point. '
                           'Add 2-3 more bullets per job, '
                           'describe tools used, and add a '
                           'Projects section.',
                'example': '',
            })
        elif word_count > 900:
            enhancements.append({
                'type':    'too_long',
                'title':   'Consider Trimming Resume',
                'issue':   f'At {word_count} words your resume '
                           f'may be too long. Keep it under 700 '
                           f'words for junior roles.',
                'fix':     'Remove oldest/least relevant '
                           'experience. Trim bullets to 1-2 '
                           'lines each.',
                'example': '',
            })

        # ── Check 7: Skills section format ────────────
        if ski_text and len(ski_text.split('\n')) < 2:
            enhancements.append({
                'type':    'skills_format',
                'title':   'Improve Skills Section Format',
                'issue':   'Your skills section may be hard for '
                           'ATS to parse if all skills are on '
                           'one line.',
                'fix':     'Organize skills by category: '
                           'Languages, Frameworks, Databases, '
                           'Tools, Soft Skills.',
                'example': (
                    'Languages: Python, JavaScript\n'
                    'Frameworks: Django, React\n'
                    'Databases: MySQL, MongoDB'
                ),
            })

        # ── Check 8: Contact info ──────────────────────
        has_linkedin = 'linkedin' in self.resume_text.lower()
        has_github   = 'github' in self.resume_text.lower()

        if not has_linkedin:
            enhancements.append({
                'type':    'missing_linkedin',
                'title':   'Add LinkedIn Profile',
                'issue':   'No LinkedIn URL found in your resume.',
                'fix':     'Add your LinkedIn URL to the contact '
                           'section. Many ATS systems and '
                           'recruiters check LinkedIn.',
                'example': 'linkedin.com/in/your-name',
            })

        if not has_github:
            enhancements.append({
                'type':    'missing_github',
                'title':   'Add GitHub Profile',
                'issue':   'No GitHub URL found. For tech roles, '
                           'GitHub is almost as important as '
                           'your resume.',
                'fix':     'Add your GitHub profile URL and make '
                           'sure your best projects are pinned '
                           'and have good README files.',
                'example': 'github.com/your-username',
            })

        # ── Generate bullet rewrites ──────────────────
        rewrites = self._generate_bullet_rewrites()

        # ── Summary suggestion ─────────────────────────
        summary_suggestion = self._suggest_summary()

        return {
            'critical':            critical,
            'improvements':        improvements,
            'enhancements':        enhancements,
            'bullet_rewrites':     rewrites,
            'summary_suggestion':  summary_suggestion,
            'keyword_suggestions': missing_keywords[:8],
        }

    # ─────────────────────────────────────────────────
    # BULLET POINT REWRITES
    # ─────────────────────────────────────────────────
    def _generate_bullet_rewrites(self):
        """
        Finds weak bullet points and rewrites them.
        """
        exp_text = self.sections.get('experience', '')
        if not exp_text:
            return []

        rewrites  = []
        lines     = exp_text.split('\n')
        jd_skills = self.jd_data.get('required_skills', [])

        for line in lines:
            line = line.strip()

            # Only process bullet-style lines
            if not line or len(line) < 20:
                continue
            if not (line.startswith('-') or
                    line.startswith('•') or
                    line[0].isupper()):
                continue

            # Clean bullet marker
            clean = line.lstrip('-•●▪ ').strip()
            if len(clean) < 15:
                continue

            issues = []
            lower  = clean.lower()

            # Check for weak verbs
            for verb in self.WEAK_VERBS:
                if re.search(r'\b' + verb + r'\b', lower):
                    issues.append('weak_verb')
                    break

            # Check for missing numbers
            if not re.search(r'\d', clean):
                issues.append('no_numbers')

            # Check if short (< 8 words)
            if len(clean.split()) < 8:
                issues.append('too_short')

            if issues and len(rewrites) < 3:
                improved = self._rewrite_bullet(
                    clean, issues, jd_skills
                )
                rewrites.append({
                    'original': clean,
                    'improved': improved,
                    'issues':   issues,
                })

        return rewrites

    def _rewrite_bullet(self, bullet, issues, jd_skills):
        """
        Rewrites a single bullet point to be stronger.
        """
        improved = bullet

        # Fix weak verb
        if 'weak_verb' in issues:
            for weak, strongs in self.STRONG_VERBS.items():
                if weak in improved.lower():
                    improved = re.sub(
                        r'\b' + weak + r'\b',
                        strongs[0],
                        improved,
                        flags=re.IGNORECASE
                    )
                    break

        # Add impact metric if missing numbers
        if 'no_numbers' in issues:
            # Add a relevant metric at the end
            skill_mentioned = next(
                (s for s in jd_skills
                 if s.lower() in improved.lower()),
                None
            )
            if skill_mentioned:
                improved += (
                    f', improving efficiency by 25%'
                )
            else:
                improved += ', resulting in measurable improvement'

        # Make it longer if too short
        if 'too_short' in issues:
            improved += (
                ' using best practices and '
                'industry-standard approaches'
            )

        return improved

    # ─────────────────────────────────────────────────
    # SUMMARY SUGGESTION
    # ─────────────────────────────────────────────────
    def _suggest_summary(self):
        """
        Generates a suggested professional summary
        based on resume skills and JD requirements.
        """
        tech_skills = self.resume_skills.get(
            'technical_skills', []
        )[:3]
        job_title   = self.jd_data.get(
            'job_level', 'Software'
        ).title()
        company     = ''

        top_skills  = ', '.join(tech_skills) if tech_skills \
                      else 'various technologies'

        matched     = self.match_result.get(
            'matched_required', []
        )[:2]
        matched_str = ' and '.join(matched) if matched else \
                      'multiple technologies'

        suggestion = (
            f'Motivated {job_title}-level developer with '
            f'hands-on experience in {top_skills}. '
            f'Proven ability to build and deploy web '
            f'applications using {matched_str}. '
            f'Passionate about clean code, performance '
            f'optimization, and delivering scalable solutions '
            f'that solve real-world problems.'
        )

        return suggestion

    # ─────────────────────────────────────────────────
    # AI-POWERED SUGGESTIONS
    # ─────────────────────────────────────────────────
    def _ai_suggestions(self):
        """
        Uses OpenAI or Gemini to generate deep,
        contextual resume suggestions.
        """
        prompt = self._build_prompt()

        if GEMINI_AVAILABLE:
            return self._call_gemini(prompt)
    
        elif OPENAI_AVAILABLE and openai_client:
            return self._call_openai(prompt)
        

        return {}

    def _build_prompt(self):
        """
        Builds the AI prompt with resume context.
        """
        missing  = self.match_result.get(
            'missing_required', []
        )
        matched  = self.match_result.get(
            'matched_required', []
        )
        score    = self.ats_score.get('overall_score', 0)
        exp_text = self.sections.get('experience', '')[:800]
        sum_text = self.sections.get('summary', '')[:300]

        return f"""You are an expert ATS resume consultant.
Analyze this resume and provide specific improvements.

RESUME SUMMARY SECTION:
{sum_text or 'NOT FOUND'}

RESUME EXPERIENCE SECTION:
{exp_text or 'NOT FOUND'}

JOB TITLE: {self.jd_data.get('job_level', 'mid').title()} Developer
REQUIRED SKILLS: {', '.join(self.jd_data.get('required_skills', [])[:8])}
CURRENT ATS SCORE: {score}/100
MATCHED SKILLS: {', '.join(matched[:5])}
MISSING SKILLS: {', '.join(missing[:5])}

Provide exactly 3 specific, actionable suggestions to improve
this resume for the target role. Focus on:
1. The most impactful change to make first
2. How to better demonstrate existing skills
3. What to add to improve the ATS score

Format your response as:
SUGGESTION 1: [title]
ISSUE: [what's wrong]
FIX: [exactly what to do]
EXAMPLE: [show the before/after text]

SUGGESTION 2: [title]
...

SUGGESTION 3: [title]
...

Keep each suggestion concise and actionable."""

    def _call_openai(self, prompt):
        """Calls OpenAI GPT-4 for suggestions."""
        try:
            response = openai_client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {
                        'role':    'system',
                        'content': (
                            'You are an expert ATS resume consultant '
                            'helping candidates improve their resumes '
                            'for specific job descriptions.'
                        ),
                    },
                    {'role': 'user', 'content': prompt},
                ],
                max_tokens=800,
                temperature=0.7,
            )
            text = response.choices[0].message.content
            return self._parse_ai_response(text)
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            return {}

    def _call_gemini(self, prompt):
        """Calls Gemini via direct REST API — your proven pattern."""
        try:
            url     = f"{GEMINI_URL}?key={GEMINI_KEY}"
            headers = {"Content-Type": "application/json"}
            data    = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }

            response = requests.post(
                url, headers=headers, json=data, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                text   = result["candidates"][0]["content"]["parts"][0]["text"]
                return self._parse_ai_response(text)
            else:
                logger.error(
                    f"Gemini error: {response.status_code} "
                    f"— {response.text[:200]}"
                )
                return {}

        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            return {}

    def _parse_ai_response(self, text):
        """
        Parses the structured AI response into a dict.
        """
        suggestions = []
        blocks      = re.split(
            r'SUGGESTION\s+\d+:', text, flags=re.IGNORECASE
        )

        for block in blocks[1:]:  # Skip first empty split
            lines  = block.strip().split('\n')
            title  = lines[0].strip() if lines else ''
            issue  = ''
            fix    = ''
            example = ''

            for line in lines[1:]:
                if line.upper().startswith('ISSUE:'):
                    issue = line[6:].strip()
                elif line.upper().startswith('FIX:'):
                    fix = line[4:].strip()
                elif line.upper().startswith('EXAMPLE:'):
                    example = line[8:].strip()

            if title and fix:
                suggestions.append({
                    'type':    'ai_suggestion',
                    'title':   title,
                    'issue':   issue,
                    'fix':     fix,
                    'example': example,
                })

        return {
            'ai_suggestions': suggestions,
            'ai_powered':     True,
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

    # ─────────────────────────────────────────────────
    # MERGE RULE + AI SUGGESTIONS
    # ─────────────────────────────────────────────────
    def _merge_suggestions(self, rule_result, ai_result):
        """
        Combines rule-based and AI suggestions.
        AI suggestions go into improvements if available.
        """
        critical     = rule_result.get('critical', [])
        improvements = rule_result.get('improvements', [])
        enhancements = rule_result.get('enhancements', [])

        # Add AI suggestions to improvements
        ai_suggestions = ai_result.get('ai_suggestions', [])
        for sug in ai_suggestions:
            improvements.insert(0, sug)

        total = (len(critical) + len(improvements) +
                 len(enhancements))

        return {
            'critical':           critical,
            'improvements':       improvements,
            'enhancements':       enhancements,
            'bullet_rewrites':    rule_result.get(
                'bullet_rewrites', []
            ),
            'summary_suggestion': rule_result.get(
                'summary_suggestion', ''
            ),
            'keyword_suggestions': rule_result.get(
                'keyword_suggestions', []
            ),
            'total_suggestions':  total,
            'ai_powered':         ai_result.get(
                'ai_powered', False
            ),
        }


# ─────────────────────────────────────────────────────
# STANDALONE HELPER
# ─────────────────────────────────────────────────────
def generate_suggestions(resume_text, sections,
                           resume_skills, jd_data,
                           match_result, ats_score):
    """
    Shortcut helper.

    Usage:
        from analyzer.services.ai_suggester import generate_suggestions
        result = generate_suggestions(...)
    """
    suggester = AISuggester(
        resume_text, sections, resume_skills,
        jd_data, match_result, ats_score
    )
    return suggester.generate()