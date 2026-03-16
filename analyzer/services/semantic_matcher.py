# analyzer/services/semantic_matcher.py

import re
import logging
import numpy as np

logger = logging.getLogger(__name__)

# ── Load sentence-transformers model ─────────────────
# We load it once at module level so it's only loaded
# into memory once (not on every request)
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    logger.info("Loading sentence-transformers model...")
    # all-MiniLM-L6-v2 is fast, small, and very accurate
    # for semantic similarity tasks
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    EMBEDDINGS_AVAILABLE = True
    logger.info("✅ Sentence transformer model loaded!")

except Exception as e:
    EMBEDDINGS_AVAILABLE = False
    embedding_model = None
    logger.warning(
        f"sentence-transformers not available: {e}. "
        f"Falling back to keyword matching."
    )


class SemanticMatcher:
    """
    Matches resume skills against JD requirements using
    AI embeddings for semantic understanding.

    Two matching strategies:
    1. Semantic (AI-powered): converts text to vectors,
       measures cosine similarity between them.
       Understands meaning and context.

    2. Keyword fallback: basic string matching used
       when the AI model isn't available.

    Usage:
        matcher = SemanticMatcher(resume_skills, jd_skills)
        result  = matcher.match()
    """

    # Threshold above which two skills are considered a match
    # 0.0 = completely different, 1.0 = identical
    # 0.55 = good balance — catches synonyms without false matches
    SIMILARITY_THRESHOLD = 0.55

    # Thresholds for match quality labels
    STRONG_MATCH  = 0.80   # Nearly identical meaning
    GOOD_MATCH    = 0.65   # Clearly related
    WEAK_MATCH    = 0.55   # Somewhat related

    def __init__(self, resume_skills, jd_required,
                 jd_preferred=None):
        """
        resume_skills: list of skills from the resume
                       e.g. ['Python', 'Django', 'MySQL']

        jd_required:   list of required skills from JD
                       e.g. ['Python', 'FastAPI', 'PostgreSQL']

        jd_preferred:  list of preferred/bonus skills (optional)
                       e.g. ['Docker', 'AWS']
        """
        self.resume_skills  = resume_skills
        self.jd_required    = jd_required
        self.jd_preferred   = jd_preferred or []

    # ─────────────────────────────────────────────────
    # MAIN METHOD
    # ─────────────────────────────────────────────────
    def match(self):
        """
        Runs semantic matching between resume and JD skills.

        Returns:
        {
            'matched_required':  [...],  # JD required skills found
            'matched_preferred': [...],  # JD preferred skills found
            'missing_required':  [...],  # JD required skills missing
            'missing_preferred': [...],  # JD preferred skills missing
            'match_details':     [...],  # Detailed per-skill results
            'required_score':    75.0,   # % of required skills matched
            'preferred_score':   50.0,   # % of preferred skills matched
            'overall_match':     70.0,   # weighted overall %
            'method': 'semantic' or 'keyword'
        }
        """
        if EMBEDDINGS_AVAILABLE and embedding_model:
            return self._semantic_match()
        else:
            logger.warning("Using keyword fallback matching")
            return self._keyword_match()

    # ─────────────────────────────────────────────────
    # STRATEGY 1: SEMANTIC MATCHING (AI-powered)
    # ─────────────────────────────────────────────────
    def _semantic_match(self):
        """
        Uses sentence-transformers to semantically match
        resume skills against JD requirements.

        Step 1: Convert all skills to embedding vectors
        Step 2: Calculate cosine similarity between each pair
        Step 3: A match is found if similarity > threshold
        """
        all_jd_skills = list(set(
            self.jd_required + self.jd_preferred
        ))

        if not all_jd_skills or not self.resume_skills:
            return self._empty_result()

        try:
            # ── Step 1: Generate embeddings ───────────
            # This converts each skill name into a
            # 384-dimensional vector of numbers
            logger.info(
                f"Generating embeddings for "
                f"{len(self.resume_skills)} resume skills and "
                f"{len(all_jd_skills)} JD skills..."
            )

            resume_embeddings = embedding_model.encode(
                self.resume_skills,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            jd_embeddings = embedding_model.encode(
                all_jd_skills,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            # ── Step 2: Calculate similarity matrix ───
            # Result shape: (num_resume_skills, num_jd_skills)
            # similarity_matrix[i][j] = how similar
            #   resume_skills[i] is to all_jd_skills[j]
            similarity_matrix = cosine_similarity(
                resume_embeddings,
                jd_embeddings
            )

            # ── Step 3: Find matches ───────────────────
            match_details = []

            for jd_idx, jd_skill in enumerate(all_jd_skills):

                # Find the best matching resume skill
                best_resume_idx   = int(
                    np.argmax(similarity_matrix[:, jd_idx])
                )
                best_similarity   = float(
                    similarity_matrix[best_resume_idx, jd_idx]
                )
                best_resume_skill = self.resume_skills[
                    best_resume_idx
                ]

                # Determine match quality
                is_match     = best_similarity >= self.SIMILARITY_THRESHOLD
                match_type   = self._get_match_type(best_similarity)
                is_required  = jd_skill in self.jd_required

                match_details.append({
                    'jd_skill':          jd_skill,
                    'best_resume_match': best_resume_skill,
                    'similarity':        round(best_similarity, 3),
                    'is_match':          is_match,
                    'match_type':        match_type,
                    'is_required':       is_required,
                })

            return self._build_result(match_details, 'semantic')

        except Exception as e:
            logger.error(f"Semantic matching failed: {e}")
            return self._keyword_match()

    # ─────────────────────────────────────────────────
    # STRATEGY 2: KEYWORD FALLBACK
    # ─────────────────────────────────────────────────
    def _keyword_match(self):
        """
        Simple keyword matching used when AI model
        isn't available.

        Still smarter than basic ATS because it handles:
        - Case insensitive matching
        - Partial matches (postgres ↔ postgresql)
        - Common aliases
        """
        ALIASES = {
            'postgres':    'postgresql',
            'js':          'javascript',
            'ts':          'typescript',
            'react':       'reactjs',
            'vue':         'vuejs',
            'node':        'nodejs',
            'k8s':         'kubernetes',
            'ml':          'machine learning',
            'dl':          'deep learning',
            'sklearn':     'scikit-learn',
            'tf':          'tensorflow',
            'gcp':         'google cloud',
            'aws':         'amazon web services',
        }

        resume_lower = [
            ALIASES.get(s.lower(), s.lower())
            for s in self.resume_skills
        ]

        match_details = []
        all_jd = list(set(self.jd_required + self.jd_preferred))

        for jd_skill in all_jd:
            jd_lower    = ALIASES.get(
                jd_skill.lower(), jd_skill.lower()
            )
            is_required = jd_skill in self.jd_required

            # Check exact match
            if jd_lower in resume_lower:
                match_details.append({
                    'jd_skill':          jd_skill,
                    'best_resume_match': self.resume_skills[
                        resume_lower.index(jd_lower)
                    ],
                    'similarity':        1.0,
                    'is_match':          True,
                    'match_type':        'exact',
                    'is_required':       is_required,
                })
                continue

            # Check partial match
            partial = next(
                (r for r in resume_lower if
                 jd_lower in r or r in jd_lower),
                None
            )
            if partial:
                idx = resume_lower.index(partial)
                match_details.append({
                    'jd_skill':          jd_skill,
                    'best_resume_match': self.resume_skills[idx],
                    'similarity':        0.75,
                    'is_match':          True,
                    'match_type':        'partial',
                    'is_required':       is_required,
                })
                continue

            # No match
            match_details.append({
                'jd_skill':          jd_skill,
                'best_resume_match': None,
                'similarity':        0.0,
                'is_match':          False,
                'match_type':        'none',
                'is_required':       is_required,
            })

        return self._build_result(match_details, 'keyword')

    # ─────────────────────────────────────────────────
    # BUILD FINAL RESULT
    # ─────────────────────────────────────────────────
    def _build_result(self, match_details, method):
        """
        Converts raw match details into a clean result dict.
        """
        matched_required  = []
        matched_preferred = []
        missing_required  = []
        missing_preferred = []

        for detail in match_details:
            jd_skill    = detail['jd_skill']
            is_match    = detail['is_match']
            is_required = detail['is_required']

            if is_required:
                if is_match:
                    matched_required.append(jd_skill)
                else:
                    missing_required.append(jd_skill)
            else:
                if is_match:
                    matched_preferred.append(jd_skill)
                else:
                    missing_preferred.append(jd_skill)

        # ── Calculate scores ──────────────────────────
        required_score = (
            len(matched_required) /
            max(len(self.jd_required), 1) * 100
        )

        preferred_score = (
            len(matched_preferred) /
            max(len(self.jd_preferred), 1) * 100
        ) if self.jd_preferred else 0

        # Overall = 80% required + 20% preferred
        overall_match = (
            required_score * 0.80 +
            preferred_score * 0.20
        )

        return {
            'matched_required':  matched_required,
            'matched_preferred': matched_preferred,
            'missing_required':  missing_required,
            'missing_preferred': missing_preferred,
            'match_details':     match_details,
            'required_score':    round(required_score, 1),
            'preferred_score':   round(preferred_score, 1),
            'overall_match':     round(overall_match, 1),
            'total_jd_skills':   len(self.jd_required) +
                                 len(self.jd_preferred),
            'total_matched':     len(matched_required) +
                                 len(matched_preferred),
            'method':            method,
        }

    # ─────────────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────────────
    def _get_match_type(self, similarity):
        """Labels a similarity score."""
        if similarity >= self.STRONG_MATCH:
            return 'strong'
        elif similarity >= self.GOOD_MATCH:
            return 'good'
        elif similarity >= self.WEAK_MATCH:
            return 'weak'
        else:
            return 'none'

    def _empty_result(self):
        """Returns empty result when no skills to match."""
        return {
            'matched_required':  [],
            'matched_preferred': [],
            'missing_required':  self.jd_required,
            'missing_preferred': self.jd_preferred,
            'match_details':     [],
            'required_score':    0.0,
            'preferred_score':   0.0,
            'overall_match':     0.0,
            'total_jd_skills':   0,
            'total_matched':     0,
            'method':            'none',
        }


# ─────────────────────────────────────────────────────
# STANDALONE HELPER
# ─────────────────────────────────────────────────────
def match_skills(resume_skills, jd_required, jd_preferred=None):
    """
    Shortcut helper.

    Usage:
        from analyzer.services.semantic_matcher import match_skills
        result = match_skills(resume_skills, jd_required)
    """
    matcher = SemanticMatcher(resume_skills, jd_required, jd_preferred)
    return matcher.match()