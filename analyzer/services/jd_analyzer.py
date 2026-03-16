# analyzer/services/jd_analyzer.py

import re
import logging

logger = logging.getLogger(__name__)


class JDAnalyzer:
    """
    Analyzes a job description and extracts structured information.

    This works WITHOUT any external AI API — it uses:
    - A large built-in skills/tools database
    - Regex patterns for experience years
    - Keyword frequency analysis
    - Rule-based education detection

    In Step 8, we'll enhance matching with AI embeddings.

    Usage:
        analyzer = JDAnalyzer(job_text)
        result = analyzer.analyze()
    """

    # ─────────────────────────────────────────────────
    # MASTER SKILLS DATABASE
    # Every skill here will be searched for in the JD
    # ─────────────────────────────────────────────────
    SKILLS_DATABASE = {

        'programming_languages': [
            'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'c',
            'ruby', 'go', 'golang', 'rust', 'swift', 'kotlin', 'php', 'scala',
            'r', 'matlab', 'perl', 'shell', 'bash', 'powershell', 'dart',
            'elixir', 'haskell', 'lua', 'groovy', 'cobol', 'fortran',
        ],

        'web_frameworks': [
            'django', 'flask', 'fastapi', 'express', 'expressjs', 'react',
            'reactjs', 'angular', 'angularjs', 'vue', 'vuejs', 'next.js',
            'nextjs', 'nuxt', 'spring', 'spring boot', 'laravel', 'rails',
            'ruby on rails', 'asp.net', 'dotnet', '.net', 'symfony',
            'nestjs', 'svelte', 'gatsby', 'remix', 'fastify', 'hapi',
        ],

        'databases': [
            'mysql', 'postgresql', 'postgres', 'sqlite', 'mongodb', 'redis',
            'elasticsearch', 'cassandra', 'dynamodb', 'oracle', 'sql server',
            'mssql', 'mariadb', 'neo4j', 'couchdb', 'firebase', 'supabase',
            'cockroachdb', 'influxdb', 'clickhouse', 'snowflake', 'bigquery',
        ],

        'cloud_devops': [
            'aws', 'amazon web services', 'azure', 'gcp', 'google cloud',
            'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins',
            'gitlab ci', 'github actions', 'circleci', 'travis ci', 'helm',
            'prometheus', 'grafana', 'nginx', 'apache', 'linux', 'unix',
            'heroku', 'vercel', 'netlify', 'digitalocean', 'cloudflare',
        ],

        'data_ml': [
            'machine learning', 'deep learning', 'tensorflow', 'pytorch',
            'keras', 'scikit-learn', 'sklearn', 'pandas', 'numpy', 'scipy',
            'matplotlib', 'seaborn', 'opencv', 'nlp', 'natural language processing',
            'computer vision', 'data science', 'data analysis', 'data engineering',
            'spark', 'hadoop', 'kafka', 'airflow', 'dbt', 'tableau', 'power bi',
            'hugging face', 'transformers', 'llm', 'langchain', 'openai',
        ],

        'tools': [
            'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence',
            'slack', 'trello', 'asana', 'figma', 'sketch', 'photoshop',
            'postman', 'swagger', 'graphql', 'rest api', 'restful',
            'microservices', 'api', 'websocket', 'grpc', 'rabbitmq',
            'celery', 'webpack', 'vite', 'babel', 'npm', 'yarn', 'pip',
            'visual studio code', 'intellij', 'pycharm', 'vim', 'excel',
        ],

        'soft_skills': [
            'communication', 'teamwork', 'leadership', 'problem solving',
            'problem-solving', 'critical thinking', 'collaboration',
            'time management', 'adaptability', 'creativity', 'attention to detail',
            'analytical', 'interpersonal', 'presentation', 'mentoring',
            'project management', 'agile', 'scrum', 'kanban',
        ],

        'testing': [
            'testing', 'unit testing', 'integration testing', 'selenium',
            'pytest', 'jest', 'mocha', 'cypress', 'playwright', 'junit',
            'test driven development', 'tdd', 'bdd', 'qa', 'quality assurance',
            'automation testing', 'manual testing', 'load testing',
        ],

        'security': [
            'cybersecurity', 'security', 'authentication', 'authorization',
            'oauth', 'jwt', 'ssl', 'tls', 'encryption', 'penetration testing',
            'vulnerability', 'sso', 'ldap', 'iam', 'zero trust',
        ],

        'mobile': [
            'android', 'ios', 'react native', 'flutter', 'swift', 'kotlin',
            'xamarin', 'ionic', 'cordova', 'mobile development',
        ],
    }

    # ─────────────────────────────────────────────────
    # EDUCATION KEYWORDS
    # ─────────────────────────────────────────────────
    EDUCATION_LEVELS = {
        'phd':        ['phd', 'ph.d', 'doctorate', 'doctoral'],
        'masters':    ['master', 'masters', 'm.s.', 'msc', 'mba', 'm.tech', 'me'],
        'bachelors':  ['bachelor', 'bachelors', 'b.s.', 'bsc', 'b.tech', 'be',
                       'undergraduate', 'b.e.'],
        'diploma':    ['diploma', 'associate', 'foundation'],
    }

    # ─────────────────────────────────────────────────
    # JOB LEVEL INDICATORS
    # ─────────────────────────────────────────────────
    LEVEL_INDICATORS = {
        'intern':   ['intern', 'internship', 'trainee', 'apprentice'],
        'junior':   ['junior', 'jr.', 'entry level', 'entry-level',
                     'fresher', 'graduate', '0-2 years', '1-2 years'],
        'mid':      ['mid level', 'mid-level', '2-4 years', '3-5 years',
                     '2+ years', '3+ years'],
        'senior':   ['senior', 'sr.', '5+ years', '6+ years', '7+ years',
                     '5-8 years', 'lead'],
        'manager':  ['manager', 'management', 'head of', 'director',
                     'vp', 'principal', 'staff engineer'],
    }

    def __init__(self, job_text):
        self.job_text = job_text
        self.job_lower = job_text.lower()

    # ─────────────────────────────────────────────────
    # MAIN METHOD
    # ─────────────────────────────────────────────────
    def analyze(self):
        """
        Main entry point. Runs all analysis steps.

        Returns a structured dictionary with everything
        extracted from the job description.
        """
        logger.info("Starting JD analysis...")

        required, preferred = self._extract_skills_by_priority()

        result = {
            # ── Core extractions ──────────────────────
            'required_skills':   required,
            'preferred_skills':  preferred,
            'all_skills':        list(set(required + preferred)),

            # ── Categorized skills ────────────────────
            'skills_by_category': self._extract_skills_by_category(),

            # ── Job metadata ──────────────────────────
            'experience_years':   self._extract_experience_years(),
            'education_level':    self._extract_education_level(),
            'job_level':          self._detect_job_level(),

            # ── Keywords ──────────────────────────────
            'keywords':           self._extract_keywords(),

            # ── Raw counts ────────────────────────────
            'total_skills_found': 0,  # filled below
            'word_count':         len(self.job_text.split()),
        }

        result['total_skills_found'] = len(result['all_skills'])

        logger.info(
            f"JD Analysis complete: "
            f"{result['total_skills_found']} skills found, "
            f"level={result['job_level']}"
        )

        return result

    # ─────────────────────────────────────────────────
    # SKILL EXTRACTION BY PRIORITY
    # ─────────────────────────────────────────────────
    def _extract_skills_by_priority(self):
        """
        Splits skills into 'required' vs 'preferred'.

        Strategy:
        - Split JD into sections by looking for
          "required", "must have", "preferred", "nice to have"
        - Extract skills from each section separately

        Returns: (required_list, preferred_list)
        """
        # ── Find "required" section ───────────────────
        required_patterns = [
            r'(?:required|must.have|mandatory|essential|'
            r'minimum qualifications?|basic qualifications?)'
            r'[\s\S]{0,500}?(?=preferred|nice.to.have|bonus|'
            r'desired|$)',
        ]

        # ── Find "preferred" section ──────────────────
        preferred_patterns = [
            r'(?:preferred|nice.to.have|bonus|desired|'
            r'plus|advantageous)'
            r'[\s\S]{0,500}?(?=required|must|$)',
        ]

        required_text  = self._extract_section_text(required_patterns)
        preferred_text = self._extract_section_text(preferred_patterns)

        # If we couldn't split, put everything in required
        if not required_text:
            required_text = self.job_lower

        required_skills  = self._find_skills_in_text(required_text)
        preferred_skills = self._find_skills_in_text(preferred_text)

        # Remove overlap — if something is "required", remove
        # it from "preferred"
        preferred_only = [
            s for s in preferred_skills
            if s not in required_skills
        ]

        return required_skills, preferred_only

    # ─────────────────────────────────────────────────
    # SKILL EXTRACTION BY CATEGORY
    # ─────────────────────────────────────────────────
    def _extract_skills_by_category(self):
        """
        Returns skills organized by category.

        Example:
        {
            'programming_languages': ['Python', 'JavaScript'],
            'databases': ['PostgreSQL', 'Redis'],
            ...
        }
        """
        result = {}

        for category, skills in self.SKILLS_DATABASE.items():
            found = []
            for skill in skills:
                if self._skill_exists_in_text(skill, self.job_lower):
                    # Store in proper case
                    found.append(self._proper_case(skill))

            if found:
                result[category] = found

        return result

    # ─────────────────────────────────────────────────
    # EXPERIENCE YEARS EXTRACTION
    # ─────────────────────────────────────────────────
    def _extract_experience_years(self):
        """
        Extracts the required years of experience.

        Handles patterns like:
        - "3+ years of experience"
        - "minimum 2 years"
        - "3-5 years experience"
        - "at least 4 years"
        """
        patterns = [
            r'(\d+)\+\s*years?',            # "3+ years"
            r'(\d+)\s*-\s*\d+\s*years?',    # "3-5 years" → takes minimum
            r'minimum\s+(\d+)\s*years?',     # "minimum 3 years"
            r'at\s+least\s+(\d+)\s*years?',  # "at least 3 years"
            r'(\d+)\s*years?\s+of\s+exp',    # "3 years of exp"
            r'experience\s+of\s+(\d+)',      # "experience of 3"
        ]

        years_found = []

        for pattern in patterns:
            matches = re.findall(pattern, self.job_lower)
            for match in matches:
                try:
                    years_found.append(int(match))
                except ValueError:
                    pass

        if not years_found:
            return 0

        # Return the most commonly mentioned value,
        # or the minimum if all different
        return min(years_found)

    # ─────────────────────────────────────────────────
    # EDUCATION LEVEL EXTRACTION
    # ─────────────────────────────────────────────────
    def _extract_education_level(self):
        """
        Detects the required education level.
        Returns: 'phd', 'masters', 'bachelors', 'diploma', or 'any'
        """
        # Check from highest to lowest
        for level, keywords in self.EDUCATION_LEVELS.items():
            for keyword in keywords:
                if keyword in self.job_lower:
                    return level

        return 'any'

    # ─────────────────────────────────────────────────
    # JOB LEVEL DETECTION
    # ─────────────────────────────────────────────────
    def _detect_job_level(self):
        """
        Detects seniority level of the role.
        Returns: 'intern', 'junior', 'mid', 'senior', 'manager'
        """
        for level, indicators in self.LEVEL_INDICATORS.items():
            for indicator in indicators:
                if indicator in self.job_lower:
                    return level

        return 'mid'  # Default assumption

    # ─────────────────────────────────────────────────
    # KEYWORD EXTRACTION
    # ─────────────────────────────────────────────────
    def _extract_keywords(self):
        """
        Extracts important non-skill keywords from the JD.
        These are domain/context words that ATS systems
        also scan for.

        Example: 'scalable', 'microservices', 'agile', 'startup'
        """
        # Words to ignore (too common, no signal value)
        STOP_WORDS = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
            'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may',
            'might', 'shall', 'can', 'not', 'no', 'nor', 'so', 'yet',
            'both', 'either', 'neither', 'each', 'few', 'more', 'most',
            'other', 'some', 'such', 'than', 'too', 'very', 'just',
            'we', 'our', 'you', 'your', 'they', 'their', 'this', 'that',
            'these', 'those', 'it', 'its', 'what', 'which', 'who',
            'whom', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
            'about', 'above', 'after', 'also', 'into', 'through',
            'during', 'before', 'while', 'although', 'because', 'since',
            'including', 'using', 'working', 'looking', 'based', 'role',
            'position', 'job', 'work', 'team', 'company', 'candidate',
            'responsibilities', 'requirements', 'qualifications',
            'experience', 'skills', 'knowledge', 'ability', 'strong',
            'good', 'excellent', 'great', 'new', 'high', 'large',
        }

        # Extract all words, filter stop words and short words
        words = re.findall(r'\b[a-zA-Z][a-zA-Z\-]{3,}\b', self.job_text)

        word_freq = {}
        for word in words:
            word_lower = word.lower()
            if word_lower not in STOP_WORDS and len(word_lower) > 3:
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

        # Sort by frequency, return top 20
        sorted_words = sorted(
            word_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [word for word, freq in sorted_words[:20]]

    # ─────────────────────────────────────────────────
    # HELPER METHODS
    # ─────────────────────────────────────────────────
    def _find_skills_in_text(self, text):
        """Find all skills from our database in a given text."""
        found = []
        text_lower = text.lower()

        for category, skills in self.SKILLS_DATABASE.items():
            for skill in skills:
                if self._skill_exists_in_text(skill, text_lower):
                    proper = self._proper_case(skill)
                    if proper not in found:
                        found.append(proper)

        return found

    def _skill_exists_in_text(self, skill, text):
        """
        Checks if a skill exists in text using word boundary matching.

        Why word boundaries?
        Without them, searching for "r" would match "error",
        "or", "for" etc. Word boundaries (\b) ensure we only
        match whole words.

        Example:
            skill = "go"
            text  = "good knowledge of golang"
            → Should NOT match "go" inside "good" or "golang"
            → \bgo\b only matches standalone "go"
        """
        try:
            pattern = r'\b' + re.escape(skill) + r'\b'
            return bool(re.search(pattern, text))
        except re.error:
            return skill in text

    def _extract_section_text(self, patterns):
        """Extract text matching any of the given regex patterns."""
        for pattern in patterns:
            match = re.search(pattern, self.job_lower, re.IGNORECASE)
            if match:
                return match.group(0)
        return ''

    def _proper_case(self, skill):
        """
        Converts skill to proper display case.

        Examples:
            'python'     → 'Python'
            'rest api'   → 'REST API'
            'aws'        → 'AWS'
            'django'     → 'Django'
            'javascript' → 'JavaScript'
        """
        # Special cases that need specific capitalization
        SPECIAL_CASES = {
            'aws': 'AWS', 'gcp': 'GCP', 'api': 'API',
            'rest api': 'REST API', 'restful': 'RESTful',
            'sql': 'SQL', 'nosql': 'NoSQL', 'mysql': 'MySQL',
            'postgresql': 'PostgreSQL', 'mongodb': 'MongoDB',
            'redis': 'Redis', 'html': 'HTML', 'css': 'CSS',
            'javascript': 'JavaScript', 'typescript': 'TypeScript',
            'nodejs': 'Node.js', 'next.js': 'Next.js',
            'reactjs': 'React', 'react': 'React',
            'vuejs': 'Vue.js', 'vue': 'Vue.js',
            'angularjs': 'Angular', 'angular': 'Angular',
            'django': 'Django', 'flask': 'Flask',
            'fastapi': 'FastAPI', 'nestjs': 'NestJS',
            'graphql': 'GraphQL', 'grpc': 'gRPC',
            'cicd': 'CI/CD', 'devops': 'DevOps',
            'mlops': 'MLOps', 'llm': 'LLM',
            'jwt': 'JWT', 'oauth': 'OAuth',
            'tdd': 'TDD', 'bdd': 'BDD', 'qa': 'QA',
            'github': 'GitHub', 'gitlab': 'GitLab',
            'linux': 'Linux', 'docker': 'Docker',
            'kubernetes': 'Kubernetes', 'k8s': 'K8s',
            'tensorflow': 'TensorFlow', 'pytorch': 'PyTorch',
            'scikit-learn': 'Scikit-learn', 'sklearn': 'Scikit-learn',
            'numpy': 'NumPy', 'pandas': 'Pandas',
            'git': 'Git', 'jira': 'Jira',
            'c++': 'C++', 'c#': 'C#', '.net': '.NET',
            'asp.net': 'ASP.NET', 'spring boot': 'Spring Boot',
            'power bi': 'Power BI', 'nlp': 'NLP',
        }

        if skill.lower() in SPECIAL_CASES:
            return SPECIAL_CASES[skill.lower()]

        # Title case for everything else
        return skill.title()


# ─────────────────────────────────────────────────────
# STANDALONE HELPER
# ─────────────────────────────────────────────────────
def analyze_job_description(job_text):
    """
    Shortcut helper function.

    Usage:
        from analyzer.services.jd_analyzer import analyze_job_description
        result = analyze_job_description(job_text)
    """
    analyzer = JDAnalyzer(job_text)
    return analyzer.analyze()