# analyzer/services/ats_scorer.py

import re
import logging

logger = logging.getLogger(__name__)


class ATSScorer:
    """
    Calculates a comprehensive ATS score from 0-100.

    Score Breakdown:
    ┌─────────────────────┬────────┬──────────────────────────┐
    │ Component           │ Weight │ What it measures         │
    ├─────────────────────┼────────┼──────────────────────────┤
    │ Skill Match         │  30%   │ Skills vs JD requirements│
    │ Keyword Match       │  25%   │ JD keywords in resume    │
    │ Experience Match    │  20%   │ Years + relevance        │
    │ Education Match     │  15%   │ Degree level match       │
    │ Format/Structure    │  10%   │ Resume completeness      │
    └─────────────────────┴────────┴──────────────────────────┘

    Usage:
        scorer = ATSScorer(
            resume_text,
            sections,
            resume_skills,
            jd_data,
            match_result
        )
        score = scorer.calculate()
    """

    # ── Score weights (must sum to 1.0) ───────────────
    WEIGHTS = {
        'skill':        0.30,
        'keyword':      0.25,
        'experience':   0.20,
        'education':    0.15,
        'format':       0.10,
    }

    # ── Grade thresholds ──────────────────────────────
    GRADES = {
        90: ('A+', 'Exceptional', '#34d399', '🏆'),
        80: ('A',  'Excellent',   '#34d399', '⭐'),
        70: ('B+', 'Good',        '#667eea', '👍'),
        60: ('B',  'Above Average','#667eea', '✅'),
        50: ('C',  'Average',     '#fbbf24', '⚠️'),
        40: ('D',  'Below Average','#f87171', '📉'),
         0: ('F',  'Poor',        '#f87171', '❌'),
    }

    def __init__(self, resume_text, sections,
                 resume_skills, jd_data, match_result):
        self.resume_text   = resume_text
        self.sections      = sections
        self.resume_skills = resume_skills
        self.jd_data       = jd_data
        self.match_result  = match_result
        self.resume_lower  = resume_text.lower()

    # ─────────────────────────────────────────────────
    # MAIN METHOD
    # ─────────────────────────────────────────────────
    def calculate(self):
        """
        Calculates all scores and returns complete result.

        Returns:
        {
            'overall_score':    74.5,
            'skill_score':      80.0,
            'keyword_score':    70.0,
            'experience_score': 75.0,
            'education_score':  100.0,
            'format_score':     60.0,
            'grade':            'B+',
            'grade_label':      'Good',
            'grade_color':      '#667eea',
            'hire_likelihood':  'Likely',
            'score_breakdown':  {...},
            'strengths':        [...],
            'weaknesses':       [...],
        }
        """

        # ── Calculate each component score ────────────
        skill_score      = self._score_skills()
        keyword_score    = self._score_keywords()
        experience_score = self._score_experience()
        education_score  = self._score_education()
        format_score     = self._score_format()

        # ── Calculate weighted overall score ──────────
        overall = (
            skill_score      * self.WEIGHTS['skill']      +
            keyword_score    * self.WEIGHTS['keyword']    +
            experience_score * self.WEIGHTS['experience'] +
            education_score  * self.WEIGHTS['education']  +
            format_score     * self.WEIGHTS['format']
        )
        overall = round(min(100, max(0, overall)), 1)

        # ── Get grade info ─────────────────────────────
        grade, label, color, emoji = self._get_grade(overall)

        # ── Hire likelihood ────────────────────────────
        hire  = self._get_hire_likelihood(overall)

        # ── Strengths and weaknesses ───────────────────
        strengths  = self._identify_strengths(
            skill_score, keyword_score,
            experience_score, education_score, format_score
        )
        weaknesses = self._identify_weaknesses(
            skill_score, keyword_score,
            experience_score, education_score, format_score
        )

        result = {
            # ── Main scores ───────────────────────────
            'overall_score':     overall,
            'skill_score':       round(skill_score, 1),
            'keyword_score':     round(keyword_score, 1),
            'experience_score':  round(experience_score, 1),
            'education_score':   round(education_score, 1),
            'format_score':      round(format_score, 1),

            # ── Grade info ────────────────────────────
            'grade':             grade,
            'grade_label':       label,
            'grade_color':       color,
            'grade_emoji':       emoji,

            # ── Hire decision ─────────────────────────
            'hire_likelihood':       hire['likelihood'],
            'hire_color':            hire['color'],
            'hire_recommendation':   hire['recommendation'],

            # ── Breakdown details ─────────────────────
            'score_breakdown': {
                'skill': {
                    'score':   round(skill_score, 1),
                    'weight':  '30%',
                    'matched': len(self.match_result.get(
                        'matched_required', [])),
                    'total':   len(self.jd_data.get(
                        'required_skills', [])),
                },
                'keyword': {
                    'score':   round(keyword_score, 1),
                    'weight':  '25%',
                },
                'experience': {
                    'score':   round(experience_score, 1),
                    'weight':  '20%',
                    'required': self.jd_data.get(
                        'experience_years', 0),
                },
                'education': {
                    'score':   round(education_score, 1),
                    'weight':  '15%',
                    'required': self.jd_data.get(
                        'education_level', 'any'),
                },
                'format': {
                    'score':   round(format_score, 1),
                    'weight':  '10%',
                    'sections_found': len([
                        s for s in
                        self.sections.keys()
                        if self.sections.get(s)
                        and not s.startswith('_')
                    ]),
                },
            },

            # ── Insights ──────────────────────────────
            'strengths':  strengths,
            'weaknesses': weaknesses,
        }

        logger.info(
            f"ATS Score calculated: {overall}/100 "
            f"(Grade: {grade})"
        )

        return result

    # ─────────────────────────────────────────────────
    # 1. SKILL SCORE (30%)
    # ─────────────────────────────────────────────────
    def _score_skills(self):
        """
        Score based on semantic skill matching results.

        Uses the output from Step 8 (SemanticMatcher).
        Required skills matter more than preferred.
        """
        if not self.match_result:
            return 0.0

        required_score  = self.match_result.get(
            'required_score', 0
        )
        preferred_score = self.match_result.get(
            'preferred_score', 0
        )

        # Required = 85%, Preferred = 15% of skill score
        skill_score = (
            required_score  * 0.85 +
            preferred_score * 0.15
        )

        return min(100, skill_score)

    # ─────────────────────────────────────────────────
    # 2. KEYWORD SCORE (25%)
    # ─────────────────────────────────────────────────
    def _score_keywords(self):
        """
        Score based on how many JD keywords appear
        in the resume.

        This simulates how basic ATS systems scan for
        specific words from the job description.
        """
        jd_keywords = self.jd_data.get('keywords', [])

        if not jd_keywords:
            return 50.0  # Neutral if no keywords extracted

        matched = 0
        for keyword in jd_keywords:
            # Check word-boundary match
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, self.resume_lower):
                matched += 1

        # Also check JD required skills as keywords
        jd_skills = self.jd_data.get('required_skills', [])
        skill_keywords_matched = 0
        for skill in jd_skills:
            if skill.lower() in self.resume_lower:
                skill_keywords_matched += 1

        # Combine keyword + skill keyword matching
        keyword_rate = matched / max(len(jd_keywords), 1)
        skill_rate   = (skill_keywords_matched /
                       max(len(jd_skills), 1))

        # Weight: 60% keyword, 40% skill-as-keyword
        keyword_score = (
            keyword_rate * 60 +
            skill_rate   * 40
        )

        return min(100, keyword_score)

    # ─────────────────────────────────────────────────
    # 3. EXPERIENCE SCORE (20%)
    # ─────────────────────────────────────────────────
    def _score_experience(self):
        """
        Score based on experience years and relevance.

        Factors:
        1. Does the resume mention experience/internship?
        2. How close is the years of experience to JD?
        3. Are the experiences relevant (same tech stack)?
        """
        score = 0.0

        # ── Factor 1: Has experience section? ─────────
        exp_text = self.sections.get('experience', '')
        if exp_text:
            score += 40  # Base score for having experience

            # Bonus for detailed experience
            if len(exp_text) > 200:
                score += 10
            if len(exp_text) > 500:
                score += 10

        # ── Factor 2: Years of experience ─────────────
        required_years = self.jd_data.get('experience_years', 0)
        resume_years   = self._extract_years_from_resume()

        if required_years == 0:
            # No specific requirement — give full marks
            score += 20
        elif resume_years >= required_years:
            score += 20  # Meets requirement
        elif resume_years >= required_years * 0.5:
            score += 10  # Partially meets
        # else: 0 bonus

        # ── Factor 3: Internship/fresher bonus ────────
        # If JD is for juniors/interns,
        # internship experience counts fully
        jd_level = self.jd_data.get('job_level', 'mid')
        if jd_level in ['intern', 'junior']:
            if 'intern' in self.resume_lower:
                score += 15
            if 'fresher' in self.resume_lower:
                score += 10

        # ── Factor 4: Relevant experience keywords ────
        exp_text_lower = exp_text.lower()
        jd_skills      = self.jd_data.get('required_skills', [])
        relevance_hits = sum(
            1 for skill in jd_skills
            if skill.lower() in exp_text_lower
        )
        relevance_bonus = min(
            15,
            relevance_hits * 3
        )
        score += relevance_bonus

        return min(100, score)

    # ─────────────────────────────────────────────────
    # 4. EDUCATION SCORE (15%)
    # ─────────────────────────────────────────────────
    def _score_education(self):
        """
        Score based on education requirements match.

        Education level hierarchy:
        phd > masters > bachelors > diploma > any
        """
        LEVEL_RANK = {
            'phd':       4,
            'masters':   3,
            'bachelors': 2,
            'diploma':   1,
            'any':       0,
        }

        jd_education = self.jd_data.get(
            'education_level', 'any'
        )
        jd_rank      = LEVEL_RANK.get(jd_education, 0)

        # If JD has no specific requirement
        if jd_rank == 0:
            return 100.0

        # Detect education level from resume
        edu_text  = (
            self.sections.get('education', '') +
            ' ' + self.resume_text
        ).lower()

        resume_rank = 0
        if any(w in edu_text for w in [
            'phd', 'ph.d', 'doctorate'
        ]):
            resume_rank = 4
        elif any(w in edu_text for w in [
            'master', 'msc', 'mba', 'm.tech', 'me'
        ]):
            resume_rank = 3
        elif any(w in edu_text for w in [
            'bachelor', 'b.tech', 'b.e', 'bsc',
            'be', 'b.e.', 'undergraduate'
        ]):
            resume_rank = 2
        elif any(w in edu_text for w in [
            'diploma', 'associate'
        ]):
            resume_rank = 1

        # Score based on gap between required and actual
        if resume_rank >= jd_rank:
            return 100.0          # Meets or exceeds
        elif resume_rank == jd_rank - 1:
            return 65.0           # One level below
        elif resume_rank == jd_rank - 2:
            return 30.0           # Two levels below
        else:
            return 10.0           # Far below requirement

    # ─────────────────────────────────────────────────
    # 5. FORMAT/STRUCTURE SCORE (10%)
    # ─────────────────────────────────────────────────
    def _score_format(self):
        """
        Score based on resume completeness and structure.

        Checks:
        - Essential sections present
        - Contact info present
        - Adequate length (not too short, not too long)
        - Has quantified achievements
        - Has action verbs
        """
        score = 0.0

        # ── Essential sections (50 points) ────────────
        essential = {
            'experience':  15,
            'education':   12,
            'skills':      13,
            'summary':     10,
        }
        for section, points in essential.items():
            if self.sections.get(section):
                score += points

        # ── Contact info present (10 points) ──────────
        has_email  = bool(re.search(
            r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
            self.resume_text
        ))
        has_phone  = bool(re.search(
            r'[\+\d][\d\s\-\(\)]{8,}',
            self.resume_text
        ))
        if has_email:
            score += 5
        if has_phone:
            score += 5

        # ── Resume length (10 points) ──────────────────
        word_count = len(self.resume_text.split())
        if 300 <= word_count <= 800:
            score += 10   # Ideal length
        elif 200 <= word_count < 300:
            score += 6    # A bit short
        elif 800 < word_count <= 1200:
            score += 6    # A bit long
        else:
            score += 2    # Too short or too long

        # ── Quantified achievements (15 points) ────────
        # Numbers in experience = quantified impact
        # e.g. "increased by 30%", "managed 5 people"
        exp_text    = self.sections.get('experience', '')
        numbers     = re.findall(r'\d+[%\+]?', exp_text)
        quant_score = min(15, len(numbers) * 3)
        score       += quant_score

        # ── Action verbs (15 points) ───────────────────
        ACTION_VERBS = [
            'built', 'developed', 'designed', 'implemented',
            'created', 'managed', 'led', 'improved', 'reduced',
            'increased', 'delivered', 'launched', 'engineered',
            'optimized', 'automated', 'architected', 'deployed',
            'integrated', 'collaborated', 'coordinated',
        ]
        exp_lower  = exp_text.lower()
        verb_count = sum(
            1 for v in ACTION_VERBS
            if v in exp_lower
        )
        verb_score = min(15, verb_count * 3)
        score      += verb_score

        return min(100, score)

    # ─────────────────────────────────────────────────
    # HELPER: Extract years from resume
    # ─────────────────────────────────────────────────
    def _extract_years_from_resume(self):
        """
        Estimates candidate's years of experience
        by looking at date patterns in experience section.
        """
        exp_text = self.sections.get('experience', '')
        if not exp_text:
            return 0

        # Look for year ranges like "2020-2023" or "2021-Present"
        year_pattern = r'(20\d{2})\s*[-–—to]+\s*(20\d{2}|present|current|now)'
        matches = re.findall(
            year_pattern,
            exp_text.lower()
        )

        if not matches:
            return 0

        total_years = 0
        import datetime
        current_year = datetime.datetime.now().year

        for start, end in matches:
            try:
                start_yr = int(start)
                end_yr   = (current_year
                            if end in ['present', 'current', 'now']
                            else int(end))
                total_years += max(0, end_yr - start_yr)
            except ValueError:
                pass

        return total_years

    # ─────────────────────────────────────────────────
    # GRADE AND HIRE LIKELIHOOD
    # ─────────────────────────────────────────────────
    def _get_grade(self, score):
        """Returns grade tuple based on score."""
        for threshold in sorted(self.GRADES.keys(), reverse=True):
            if score >= threshold:
                return self.GRADES[threshold]
        return self.GRADES[0]

    def _get_hire_likelihood(self, score):
        """Returns hire likelihood based on overall score."""
        if score >= 80:
            return {
                'likelihood':     'Very Likely',
                'color':          '#34d399',
                'recommendation': (
                    'Strong candidate. Recommend for interview.'
                ),
            }
        elif score >= 65:
            return {
                'likelihood':     'Likely',
                'color':          '#667eea',
                'recommendation': (
                    'Good candidate. Consider for interview '
                    'with skill gap review.'
                ),
            }
        elif score >= 50:
            return {
                'likelihood':     'Possible',
                'color':          '#fbbf24',
                'recommendation': (
                    'Borderline candidate. Interview only if '
                    'shortage of applicants.'
                ),
            }
        else:
            return {
                'likelihood':     'Unlikely',
                'color':          '#f87171',
                'recommendation': (
                    'Resume needs significant improvement '
                    'before applying to this role.'
                ),
            }

    # ─────────────────────────────────────────────────
    # STRENGTHS AND WEAKNESSES
    # ─────────────────────────────────────────────────
    def _identify_strengths(self, skill, keyword,
                             experience, education, fmt):
        """Identifies top scoring areas as strengths."""
        strengths = []

        if skill >= 70:
            matched = len(self.match_result.get(
                'matched_required', []
            ))
            strengths.append(
                f"Strong skill match — {matched} required "
                f"skills found on your resume"
            )
        if keyword >= 70:
            strengths.append(
                "Good keyword coverage — your resume uses "
                "language that ATS systems look for"
            )
        if experience >= 70:
            strengths.append(
                "Solid experience section with relevant "
                "work history"
            )
        if education >= 80:
            strengths.append(
                "Education meets or exceeds job requirements"
            )
        if fmt >= 70:
            strengths.append(
                "Well-structured resume with clear sections "
                "and quantified achievements"
            )

        return strengths or [
            "Resume uploaded successfully — "
            "improvements will raise your score"
        ]

    def _identify_weaknesses(self, skill, keyword,
                              experience, education, fmt):
        """Identifies low scoring areas as weaknesses."""
        weaknesses = []

        if skill < 50:
            missing = self.match_result.get(
                'missing_required', []
            )[:3]
            weaknesses.append(
                f"Missing key skills: "
                f"{', '.join(missing) if missing else 'several required skills'}"
            )
        if keyword < 50:
            weaknesses.append(
                "Low keyword match — add more terms "
                "from the job description to your resume"
            )
        if experience < 50:
            weaknesses.append(
                "Experience section needs more detail — "
                "add quantified achievements and metrics"
            )
        if education < 60:
            weaknesses.append(
                f"Education level may not meet requirements "
                f"({self.jd_data.get('education_level', 'unknown')} required)"
            )
        if fmt < 50:
            weaknesses.append(
                "Resume structure needs improvement — "
                "add missing sections and action verbs"
            )

        return weaknesses


# ─────────────────────────────────────────────────────
# STANDALONE HELPER
# ─────────────────────────────────────────────────────
def calculate_ats_score(resume_text, sections,
                         resume_skills, jd_data,
                         match_result):
    """
    Shortcut helper function.

    Usage:
        from analyzer.services.ats_scorer import calculate_ats_score
        result = calculate_ats_score(...)
    """
    scorer = ATSScorer(
        resume_text, sections,
        resume_skills, jd_data, match_result
    )
    return scorer.calculate()