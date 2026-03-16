# analyzer/services/skill_extractor.py

import re
import logging

logger = logging.getLogger(__name__)

# ── Try to import spaCy ───────────────────────────────
# We wrap in try/except so the app doesn't crash
# if spaCy isn't installed
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
    SPACY_AVAILABLE = True
    logger.info("spaCy loaded successfully")
except Exception as e:
    SPACY_AVAILABLE = False
    logger.warning(f"spaCy not available: {e}. "
                   f"Using database-only extraction.")


class SkillExtractor:
    """
    Extracts skills from resume text using multiple methods.

    Method 1 — Database matching:
        Check if known skills appear in the text.
        Fast and accurate for known skills.

    Method 2 — spaCy NLP:
        Use language model to find noun phrases
        that might be skills we haven't seen before.

    Method 3 — Section-aware:
        Skills found in the Skills section get a
        higher confidence score than those found
        only in the Experience section.

    Usage:
        extractor = SkillExtractor(resume_text, sections)
        result = extractor.extract()
    """

    # ─────────────────────────────────────────────────
    # RESUME SKILLS DATABASE
    # Same structure as JD analyzer for easy comparison
    # ─────────────────────────────────────────────────
    SKILLS_DATABASE = {

        'programming_languages': [
            'python', 'javascript', 'typescript', 'java', 'c++', 'c#',
            'c', 'ruby', 'go', 'golang', 'rust', 'swift', 'kotlin',
            'php', 'scala', 'r', 'matlab', 'perl', 'shell', 'bash',
            'powershell', 'dart', 'elixir', 'haskell', 'lua', 'groovy',
        ],

        'web_frameworks': [
            'django', 'flask', 'fastapi', 'express', 'expressjs',
            'react', 'reactjs', 'angular', 'angularjs', 'vue', 'vuejs',
            'next.js', 'nextjs', 'nuxt', 'spring', 'spring boot',
            'laravel', 'rails', 'ruby on rails', 'asp.net', '.net',
            'dotnet', 'nestjs', 'svelte', 'gatsby',
        ],

        'databases': [
            'mysql', 'postgresql', 'postgres', 'sqlite', 'mongodb',
            'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'oracle',
            'sql server', 'mssql', 'mariadb', 'neo4j', 'firebase',
            'supabase', 'snowflake', 'bigquery',
        ],

        'cloud_devops': [
            'aws', 'amazon web services', 'azure', 'gcp', 'google cloud',
            'docker', 'kubernetes', 'k8s', 'terraform', 'ansible',
            'jenkins', 'gitlab ci', 'github actions', 'circleci',
            'helm', 'prometheus', 'grafana', 'nginx', 'apache',
            'linux', 'unix', 'heroku', 'vercel', 'netlify',
        ],

        'data_ml': [
            'machine learning', 'deep learning', 'tensorflow', 'pytorch',
            'keras', 'scikit-learn', 'sklearn', 'pandas', 'numpy',
            'scipy', 'matplotlib', 'seaborn', 'opencv', 'nlp',
            'natural language processing', 'computer vision',
            'data science', 'data analysis', 'spark', 'hadoop',
            'kafka', 'airflow', 'tableau', 'power bi', 'hugging face',
            'transformers', 'llm', 'langchain', 'openai',
        ],

        'tools': [
            'git', 'github', 'gitlab', 'bitbucket', 'jira',
            'confluence', 'postman', 'swagger', 'graphql', 'rest api',
            'restful', 'microservices', 'websocket', 'grpc',
            'rabbitmq', 'celery', 'webpack', 'vite', 'npm', 'yarn',
            'visual studio code', 'intellij', 'pycharm', 'excel',
            'advanced excel',
        ],

        'soft_skills': [
            'communication', 'teamwork', 'leadership',
            'problem solving', 'problem-solving', 'critical thinking',
            'collaboration', 'time management', 'adaptability',
            'creativity', 'attention to detail', 'analytical',
            'interpersonal', 'presentation', 'mentoring',
            'project management', 'agile', 'scrum',
        ],

        'testing': [
            'testing', 'unit testing', 'integration testing',
            'selenium', 'pytest', 'jest', 'cypress', 'playwright',
            'junit', 'tdd', 'bdd', 'qa', 'automation testing',
        ],

        'security': [
            'authentication', 'authorization', 'oauth', 'jwt',
            'ssl', 'encryption', 'cybersecurity', 'iam',
        ],

        'mobile': [
            'android', 'ios', 'react native', 'flutter',
            'mobile development',
        ],
    }

    # ─────────────────────────────────────────────────
    # SECTION CONFIDENCE WEIGHTS
    # Skills found in the Skills section are more
    # reliable than those found in Experience
    # ─────────────────────────────────────────────────
    SECTION_WEIGHTS = {
        'skills':       1.0,   # Highest confidence
        'experience':   0.85,  # High — mentioned in work context
        'projects':     0.80,  # Good — used in real project
        'summary':      0.70,  # Medium — self-claimed
        'certifications': 0.90, # High — certified in it
        'education':    0.60,  # Lower — might just be coursework
        'other':        0.50,  # Lowest — unknown context
    }

    def __init__(self, resume_text, sections=None):
        """
        resume_text: full cleaned resume text
        sections:    dict from SectionDetector (optional)
                     If provided, enables section-aware extraction
        """
        self.resume_text = resume_text
        self.sections    = sections or {}
        self.text_lower  = resume_text.lower()

    # ─────────────────────────────────────────────────
    # MAIN METHOD
    # ─────────────────────────────────────────────────
    def extract(self):
        """
        Runs all extraction methods and combines results.

        Returns:
        {
            'technical_skills': [...],
            'tools':            [...],
            'soft_skills':      [...],
            'all_skills':       [...],
            'by_category':      {...},
            'skill_confidence': {'Python': 0.95, ...},
            'extraction_method': 'database+spacy' or 'database'
        }
        """
        # ── Method 1: Database matching ───────────────
        db_skills, confidence = self._extract_by_database()

        # ── Method 2: spaCy NLP extraction ───────────
        nlp_skills = []
        if SPACY_AVAILABLE:
            nlp_skills = self._extract_by_spacy()
            # Add any new skills found by spaCy
            for skill in nlp_skills:
                if skill not in confidence:
                    confidence[skill] = 0.60  # Lower confidence
                    # for NLP-discovered skills

        # ── Combine all skills ────────────────────────
        all_skills = list(confidence.keys())

        # ── Organize by category ─────────────────────
        by_category = self._organize_by_category(all_skills)

        # ── Split into types ──────────────────────────
        technical = self._get_technical_skills(by_category)
        tools     = by_category.get('tools', [])
        soft      = by_category.get('soft_skills', [])

        method = 'database+spacy' if SPACY_AVAILABLE else 'database'

        result = {
            'technical_skills':  technical,
            'tools':             tools,
            'soft_skills':       soft,
            'all_skills':        all_skills,
            'by_category':       by_category,
            'skill_confidence':  confidence,
            'total_found':       len(all_skills),
            'extraction_method': method,
        }

        logger.info(
            f"Extracted {len(all_skills)} skills "
            f"using {method}"
        )

        return result

    # ─────────────────────────────────────────────────
    # METHOD 1: DATABASE MATCHING
    # ─────────────────────────────────────────────────
    def _extract_by_database(self):
        """
        Scans resume text for every skill in our database.

        Returns:
            skills_list: list of found skill names
            confidence:  dict of {skill: confidence_score}
        """
        confidence = {}

        for category, skills in self.SKILLS_DATABASE.items():
            for skill in skills:

                # Check if skill exists in full resume
                if not self._skill_in_text(skill, self.text_lower):
                    continue

                # Skill found — now calculate confidence
                # based on WHERE it appears
                score = self._calculate_confidence(skill)
                proper_name = self._proper_case(skill)
                confidence[proper_name] = round(score, 2)

        return list(confidence.keys()), confidence

    def _calculate_confidence(self, skill):
        """
        Calculates confidence score for a skill based on
        which sections it appears in.

        Logic:
        - Start with base score from highest-weighted section
        - Bonus for appearing in multiple sections
        - Bonus for appearing multiple times
        """
        best_score  = 0.0
        appearances = 0

        # Check each section
        for section_name, section_text in self.sections.items():
            if section_name.startswith('_'):
                continue
            if not section_text:
                continue

            section_lower = section_text.lower()
            if self._skill_in_text(skill, section_lower):
                weight = self.SECTION_WEIGHTS.get(section_name, 0.5)
                best_score = max(best_score, weight)
                appearances += section_lower.count(skill.lower())

        # If no section data, use full text
        if best_score == 0.0:
            if self._skill_in_text(skill, self.text_lower):
                best_score  = 0.65
                appearances = self.text_lower.count(skill.lower())

        # Bonus for multiple appearances (max +0.1)
        appearance_bonus = min(0.1, appearances * 0.02)
        final_score = min(1.0, best_score + appearance_bonus)

        return final_score

    # ─────────────────────────────────────────────────
    # METHOD 2: spaCy NLP EXTRACTION
    # ─────────────────────────────────────────────────
    def _extract_by_spacy(self):
        """
        Uses spaCy's language model to find noun phrases
        that might be technical skills.

        spaCy reads text like a human — it understands
        grammar and can identify "noun phrases" like:
        "machine learning algorithms"
        "REST API endpoints"
        "agile development methodology"

        We then filter these to find tech-sounding phrases.
        """
        # Use a shorter version to avoid processing limits
        text_sample = self.resume_text[:3000]

        try:
            doc = nlp(text_sample)
        except Exception as e:
            logger.warning(f"spaCy processing failed: {e}")
            return []

        tech_indicators = {
            # If a noun phrase contains these words,
            # it's likely a technical skill
            'api', 'framework', 'database', 'system', 'server',
            'cloud', 'service', 'platform', 'tool', 'language',
            'library', 'stack', 'architecture', 'algorithm',
            'model', 'pipeline', 'deployment', 'integration',
            'development', 'engineering', 'automation',
        }

        found_skills = []

        # ── Check noun chunks (noun phrases) ─────────
        for chunk in doc.noun_chunks:
            text = chunk.text.strip().lower()

            # Skip very short or very long phrases
            if len(text) < 2 or len(text) > 40:
                continue

            # Skip if it's just a pronoun or article
            if text in {'the', 'a', 'an', 'i', 'we', 'my', 'our'}:
                continue

            # Check if it sounds technical
            is_technical = any(
                indicator in text
                for indicator in tech_indicators
            )

            if is_technical:
                proper = text.title()
                if proper not in found_skills:
                    found_skills.append(proper)

        # ── Check named entities ──────────────────────
        # spaCy can detect organization names, products etc.
        # which often overlap with tech tools (e.g. "GitHub")
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT']:
                text = ent.text.strip()
                if len(text) > 1 and text not in found_skills:
                    found_skills.append(text)

        return found_skills[:20]  # Cap at 20

    # ─────────────────────────────────────────────────
    # ORGANIZE BY CATEGORY
    # ─────────────────────────────────────────────────
    def _organize_by_category(self, all_skills):
        """
        Given a flat list of skills, group them by category.
        """
        by_category = {}
        all_skills_lower = [s.lower() for s in all_skills]

        for category, db_skills in self.SKILLS_DATABASE.items():
            found_in_cat = []
            for db_skill in db_skills:
                proper = self._proper_case(db_skill)
                if (proper in all_skills or
                        db_skill.lower() in all_skills_lower):
                    found_in_cat.append(proper)

            if found_in_cat:
                by_category[category] = found_in_cat

        return by_category

    def _get_technical_skills(self, by_category):
        """Returns all skills except soft skills and tools."""
        tech_categories = [
            'programming_languages', 'web_frameworks',
            'databases', 'cloud_devops', 'data_ml',
            'testing', 'security', 'mobile',
        ]
        result = []
        for cat in tech_categories:
            result.extend(by_category.get(cat, []))
        return result

    # ─────────────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────────────
    def _skill_in_text(self, skill, text):
        """Word-boundary safe skill search."""
        try:
            pattern = r'\b' + re.escape(skill) + r'\b'
            return bool(re.search(pattern, text))
        except re.error:
            return skill in text

    def _proper_case(self, skill):
        """Converts skill to proper display name."""
        SPECIAL_CASES = {
            'aws': 'AWS', 'gcp': 'GCP', 'api': 'API',
            'rest api': 'REST API', 'restful': 'RESTful',
            'sql': 'SQL', 'nosql': 'NoSQL', 'mysql': 'MySQL',
            'postgresql': 'PostgreSQL', 'mongodb': 'MongoDB',
            'redis': 'Redis', 'html': 'HTML', 'css': 'CSS',
            'javascript': 'JavaScript', 'typescript': 'TypeScript',
            'reactjs': 'React', 'react': 'React',
            'vuejs': 'Vue.js', 'vue': 'Vue.js',
            'angularjs': 'Angular', 'angular': 'Angular',
            'django': 'Django', 'flask': 'Flask',
            'fastapi': 'FastAPI', 'nestjs': 'NestJS',
            'graphql': 'GraphQL', 'grpc': 'gRPC',
            'jwt': 'JWT', 'oauth': 'OAuth',
            'tdd': 'TDD', 'bdd': 'BDD', 'qa': 'QA',
            'github': 'GitHub', 'gitlab': 'GitLab',
            'linux': 'Linux', 'docker': 'Docker',
            'kubernetes': 'Kubernetes', 'k8s': 'K8s',
            'tensorflow': 'TensorFlow', 'pytorch': 'PyTorch',
            'scikit-learn': 'Scikit-learn',
            'sklearn': 'Scikit-learn',
            'numpy': 'NumPy', 'pandas': 'Pandas',
            'git': 'Git', 'jira': 'Jira',
            'c++': 'C++', 'c#': 'C#', '.net': '.NET',
            'spring boot': 'Spring Boot',
            'power bi': 'Power BI', 'nlp': 'NLP',
            'next.js': 'Next.js', 'nodejs': 'Node.js',
            'advanced excel': 'Advanced Excel',
        }
        return SPECIAL_CASES.get(skill.lower(), skill.title())


# ─────────────────────────────────────────────────────
# STANDALONE HELPER
# ─────────────────────────────────────────────────────
def extract_resume_skills(resume_text, sections=None):
    """
    Shortcut helper function.

    Usage:
        from analyzer.services.skill_extractor import extract_resume_skills
        result = extract_resume_skills(resume_text, sections)
    """
    extractor = SkillExtractor(resume_text, sections)
    return extractor.extract()