# analyzer/services/gap_analyzer.py

import logging

logger = logging.getLogger(__name__)


class GapAnalyzer:
    """
    Analyzes the skill gap between resume and job requirements.

    Takes the missing skills from SemanticMatcher (Step 8)
    and enriches each one with:
    - Importance level (how critical it is for the role)
    - Difficulty to learn
    - Time to learn
    - Free learning resources
    - Related skills the candidate already has
    - Priority order for learning

    Usage:
        analyzer = GapAnalyzer(
            missing_skills,
            resume_skills,
            jd_data
        )
        result = analyzer.analyze()
    """

    # ─────────────────────────────────────────────────
    # SKILL KNOWLEDGE BASE
    # Every skill has metadata about how hard it is
    # to learn, how long it takes, and where to learn it
    # ─────────────────────────────────────────────────
    SKILL_KNOWLEDGE = {

        # ── Programming Languages ─────────────────────
        'python': {
            'difficulty':   'Easy',
            'learn_time':   '4-6 weeks',
            'category':     'programming_languages',
            'resources': [
                'python.org/doc (Official Docs)',
                'Real Python — realpython.com',
                'Automate the Boring Stuff — free online',
            ],
            'related':      ['javascript', 'ruby', 'php'],
            'tip': 'Start with official Python tutorial, '
                   'then build small projects.',
        },
        'javascript': {
            'difficulty':   'Medium',
            'learn_time':   '6-8 weeks',
            'category':     'programming_languages',
            'resources': [
                'javascript.info (best free resource)',
                'MDN Web Docs — developer.mozilla.org',
                'freeCodeCamp JavaScript Course',
            ],
            'related':      ['typescript', 'python', 'html'],
            'tip': 'Learn DOM manipulation and async/await '
                   'early — very common in interviews.',
        },
        'typescript': {
            'difficulty':   'Medium',
            'learn_time':   '2-3 weeks',
            'category':     'programming_languages',
            'resources': [
                'typescriptlang.org/docs (Official)',
                'TypeScript Deep Dive — free online book',
            ],
            'related':      ['javascript'],
            'tip': 'TypeScript is just JavaScript with types. '
                   'Learn JS first, TS becomes easy.',
        },
        'java': {
            'difficulty':   'Medium',
            'learn_time':   '8-12 weeks',
            'category':     'programming_languages',
            'resources': [
                'docs.oracle.com/javase (Official)',
                'Java Programming MOOC — mooc.fi',
                'Codecademy Java Course',
            ],
            'related':      ['c#', 'kotlin', 'scala'],
            'tip': 'Focus on OOP concepts — they are the '
                   'foundation of Java development.',
        },

        # ── Web Frameworks ────────────────────────────
        'django': {
            'difficulty':   'Medium',
            'learn_time':   '3-4 weeks',
            'category':     'web_frameworks',
            'resources': [
                'docs.djangoproject.com (Official)',
                'Django Girls Tutorial — free',
                'Django for Beginners — William Vincent',
            ],
            'related':      ['python', 'flask', 'fastapi'],
            'tip': 'Build a blog or todo app first. '
                   'Django follows MVT pattern.',
        },
        'fastapi': {
            'difficulty':   'Easy',
            'learn_time':   '1-2 weeks',
            'category':     'web_frameworks',
            'resources': [
                'fastapi.tiangolo.com (Official — excellent)',
                'FastAPI Full Course — YouTube',
            ],
            'related':      ['python', 'django', 'flask'],
            'tip': 'If you know Python and Django, '
                   'FastAPI takes only a few days.',
        },
        'flask': {
            'difficulty':   'Easy',
            'learn_time':   '1-2 weeks',
            'category':     'web_frameworks',
            'resources': [
                'flask.palletsprojects.com (Official)',
                'Flask Mega-Tutorial — Miguel Grinberg',
            ],
            'related':      ['python', 'django'],
            'tip': 'Much simpler than Django. '
                   'Great for APIs and microservices.',
        },
        'react': {
            'difficulty':   'Medium',
            'learn_time':   '4-6 weeks',
            'category':     'web_frameworks',
            'resources': [
                'react.dev (Official — newly redesigned)',
                'Scrimba React Course — free',
                'Full Stack Open — fullstackopen.com',
            ],
            'related':      ['javascript', 'typescript', 'html'],
            'tip': 'Master JavaScript fundamentals first. '
                   'React hooks are the most important concept.',
        },
        'spring boot': {
            'difficulty':   'Hard',
            'learn_time':   '6-8 weeks',
            'category':     'web_frameworks',
            'resources': [
                'spring.io/guides (Official)',
                'Spring Boot Tutorial — Amigoscode YouTube',
            ],
            'related':      ['java', 'maven', 'gradle'],
            'tip': 'Learn Java OOP and Maven first. '
                   'Spring Boot makes Java web dev much easier.',
        },

        # ── Databases ─────────────────────────────────
        'postgresql': {
            'difficulty':   'Easy',
            'learn_time':   '1-2 weeks',
            'category':     'databases',
            'resources': [
                'postgresql.org/docs (Official)',
                'PostgreSQL Tutorial — postgresqltutorial.com',
            ],
            'related':      ['mysql', 'sqlite', 'sql'],
            'tip': 'Very similar to MySQL. '
                   'Main difference is advanced features like JSONB.',
        },
        'mongodb': {
            'difficulty':   'Easy',
            'learn_time':   '1-2 weeks',
            'category':     'databases',
            'resources': [
                'mongodb.com/docs (Official)',
                'MongoDB University — free courses',
            ],
            'related':      ['mysql', 'postgresql', 'redis'],
            'tip': 'Focus on aggregation pipeline — '
                   'it is the most powerful MongoDB feature.',
        },
        'redis': {
            'difficulty':   'Easy',
            'learn_time':   '1 week',
            'category':     'databases',
            'resources': [
                'redis.io/docs (Official)',
                'Redis University — university.redis.com',
            ],
            'related':      ['mongodb', 'postgresql'],
            'tip': 'Mainly used for caching and sessions. '
                   'Learn the 5 data types first.',
        },
        'mysql': {
            'difficulty':   'Easy',
            'learn_time':   '2-3 weeks',
            'category':     'databases',
            'resources': [
                'dev.mysql.com/doc (Official)',
                'MySQL Tutorial — mysqltutorial.org',
                'W3Schools SQL Tutorial',
            ],
            'related':      ['postgresql', 'sqlite', 'sql'],
            'tip': 'SQL is the same across databases. '
                   'Learn SELECT, JOIN, GROUP BY first.',
        },

        # ── Cloud & DevOps ────────────────────────────
        'docker': {
            'difficulty':   'Medium',
            'learn_time':   '2-3 weeks',
            'category':     'cloud_devops',
            'resources': [
                'docs.docker.com (Official)',
                'Docker 101 Tutorial — play-with-docker.com',
                'TechWorld with Nana — YouTube (free)',
            ],
            'related':      ['linux', 'kubernetes', 'git'],
            'tip': 'Start with Dockerfile and docker-compose. '
                   'You do not need Kubernetes yet.',
        },
        'kubernetes': {
            'difficulty':   'Hard',
            'learn_time':   '4-8 weeks',
            'category':     'cloud_devops',
            'resources': [
                'kubernetes.io/docs (Official)',
                'Kubernetes for Beginners — KodeKloud',
                'TechWorld with Nana K8s Course — YouTube',
            ],
            'related':      ['docker', 'linux', 'aws'],
            'tip': 'Learn Docker first — Kubernetes is '
                   'Docker at scale. Start with minikube locally.',
        },
        'aws': {
            'difficulty':   'Hard',
            'learn_time':   '2-3 months',
            'category':     'cloud_devops',
            'resources': [
                'aws.amazon.com/training (Free Tier available)',
                'A Cloud Guru — acloudguru.com',
                'AWS Skill Builder — free official courses',
            ],
            'related':      ['linux', 'docker', 'gcp'],
            'tip': 'Start with S3, EC2, and IAM. '
                   'AWS Free Tier lets you practice for free.',
        },
        'gcp': {
            'difficulty':   'Hard',
            'learn_time':   '2-3 months',
            'category':     'cloud_devops',
            'resources': [
                'cloud.google.com/docs (Official)',
                'Google Cloud Skills Boost — free courses',
            ],
            'related':      ['aws', 'docker', 'linux'],
            'tip': 'GCP gives $300 free credits. '
                   'Start with Cloud Run and BigQuery.',
        },
        'azure': {
            'difficulty':   'Hard',
            'learn_time':   '2-3 months',
            'category':     'cloud_devops',
            'resources': [
                'learn.microsoft.com/azure (Free paths)',
                'Microsoft Azure Fundamentals AZ-900',
            ],
            'related':      ['aws', 'docker', 'dotnet'],
            'tip': 'AZ-900 certification is free to study for '
                   'and recognized by most companies.',
        },
        'linux': {
            'difficulty':   'Medium',
            'learn_time':   '3-4 weeks',
            'category':     'cloud_devops',
            'resources': [
                'linuxcommand.org (free)',
                'The Linux Command Line — free book online',
                'OverTheWire Bandit — wargames for practice',
            ],
            'related':      ['bash', 'docker', 'aws'],
            'tip': 'Focus on file system, permissions, '
                   'and bash scripting. Used in every DevOps role.',
        },
        'git': {
            'difficulty':   'Easy',
            'learn_time':   '3-5 days',
            'category':     'tools',
            'resources': [
                'git-scm.com/doc (Official)',
                'Learn Git Branching — learngitbranching.js.org',
                'GitHub Skills — skills.github.com',
            ],
            'related':      ['github', 'gitlab'],
            'tip': 'Learn: clone, add, commit, push, pull, '
                   'branch, merge. That covers 90% of daily use.',
        },

        # ── AI / ML ───────────────────────────────────
        'machine learning': {
            'difficulty':   'Hard',
            'learn_time':   '3-6 months',
            'category':     'data_ml',
            'resources': [
                'Coursera ML Specialization — Andrew Ng (free audit)',
                'fast.ai — practical deep learning (free)',
                'scikit-learn.org/stable/tutorial',
            ],
            'related':      ['python', 'numpy', 'pandas'],
            'tip': 'Start with scikit-learn for classical ML '
                   'before jumping to deep learning.',
        },
        'tensorflow': {
            'difficulty':   'Hard',
            'learn_time':   '4-8 weeks',
            'category':     'data_ml',
            'resources': [
                'tensorflow.org/tutorials (Official)',
                'Deep Learning Specialization — Coursera',
            ],
            'related':      ['python', 'keras', 'numpy'],
            'tip': 'Use Keras API (built into TensorFlow). '
                   'Start with image classification.',
        },
        'pytorch': {
            'difficulty':   'Hard',
            'learn_time':   '4-8 weeks',
            'category':     'data_ml',
            'resources': [
                'pytorch.org/tutorials (Official)',
                'Deep Learning with PyTorch — free book',
            ],
            'related':      ['python', 'numpy', 'tensorflow'],
            'tip': 'More Pythonic than TensorFlow. '
                   'Preferred in research. Learn autograd first.',
        },
        'pandas': {
            'difficulty':   'Easy',
            'learn_time':   '1-2 weeks',
            'category':     'data_ml',
            'resources': [
                'pandas.pydata.org/docs (Official)',
                'Kaggle Pandas Course — free',
            ],
            'related':      ['python', 'numpy', 'matplotlib'],
            'tip': 'Focus on DataFrame operations, '
                   'groupby, and merge. Most used data tool.',
        },

        # ── Tools ─────────────────────────────────────
        'graphql': {
            'difficulty':   'Medium',
            'learn_time':   '1-2 weeks',
            'category':     'tools',
            'resources': [
                'graphql.org/learn (Official)',
                'How to GraphQL — howtographql.com (free)',
            ],
            'related':      ['rest api', 'javascript', 'nodejs'],
            'tip': 'Think of it as a flexible alternative '
                   'to REST. Learn queries and mutations first.',
        },
        'rest api': {
            'difficulty':   'Easy',
            'learn_time':   '1 week',
            'category':     'tools',
            'resources': [
                'restfulapi.net (concepts)',
                'Build REST APIs with Django REST Framework',
                'Postman Learning Center — learning.postman.com',
            ],
            'related':      ['http', 'json', 'django'],
            'tip': 'REST is a design pattern, not a technology. '
                   'Learn HTTP methods and status codes.',
        },
        'microservices': {
            'difficulty':   'Hard',
            'learn_time':   '4-8 weeks',
            'category':     'tools',
            'resources': [
                'microservices.io (patterns)',
                'Sam Newman — Building Microservices (book)',
                'Docker + Kubernetes tutorials',
            ],
            'related':      ['docker', 'kubernetes', 'rest api'],
            'tip': 'Understand the problems first (monolith pain '
                   'points), then learn the solutions.',
        },

        # ── Testing ───────────────────────────────────
        'pytest': {
            'difficulty':   'Easy',
            'learn_time':   '3-5 days',
            'category':     'testing',
            'resources': [
                'docs.pytest.org (Official)',
                'Python Testing with pytest — book',
            ],
            'related':      ['python', 'unittest'],
            'tip': 'Learn fixtures and parametrize. '
                   'Write tests alongside every feature you build.',
        },
        'selenium': {
            'difficulty':   'Medium',
            'learn_time':   '2-3 weeks',
            'category':     'testing',
            'resources': [
                'selenium-python.readthedocs.io',
                'Selenium WebDriver Tutorial — official',
            ],
            'related':      ['python', 'testing', 'javascript'],
            'tip': 'Consider Playwright as a modern alternative '
                   'to Selenium — it has better Python support.',
        },
    }

    # ─────────────────────────────────────────────────
    # IMPORTANCE LEVELS
    # How critical is this skill for the role?
    # ─────────────────────────────────────────────────
    IMPORTANCE_LEVELS = {
        'Critical':   {
            'color': '#f87171',
            'bg':    'rgba(248,113,113,0.1)',
            'border':'rgba(248,113,113,0.25)',
            'description': 'Required for the role. '
                           'Must have to pass ATS screening.',
        },
        'Important':  {
            'color': '#fbbf24',
            'bg':    'rgba(251,191,36,0.1)',
            'border':'rgba(251,191,36,0.25)',
            'description': 'Strongly preferred. '
                           'Will significantly boost your chances.',
        },
        'Nice to Have': {
            'color': '#34d399',
            'bg':    'rgba(52,211,153,0.1)',
            'border':'rgba(52,211,153,0.25)',
            'description': 'Bonus skill. Nice to have '
                           'but not a dealbreaker.',
        },
    }

    def __init__(self, missing_skills, resume_skills,
                 jd_data, match_result=None):
        """
        missing_skills: list of skills missing from resume
        resume_skills:  dict from SkillExtractor
        jd_data:        dict from JDAnalyzer
        match_result:   dict from SemanticMatcher (optional)
        """
        self.missing_skills = missing_skills
        self.resume_skills  = resume_skills
        self.jd_data        = jd_data
        self.match_result   = match_result or {}
        self.all_resume     = [
            s.lower() for s in
            resume_skills.get('all_skills', [])
        ]

    # ─────────────────────────────────────────────────
    # MAIN METHOD
    # ─────────────────────────────────────────────────
    def analyze(self):
        """
        Runs the full gap analysis.

        Returns:
        {
            'skill_gaps':      [...detailed gap objects],
            'critical_gaps':   [...critical missing skills],
            'important_gaps':  [...important missing skills],
            'minor_gaps':      [...nice-to-have missing skills],
            'gap_severity':    'Critical'/'Moderate'/'Minor',
            'readiness_score': 72,
            'action_plan':     [...prioritized learning steps],
            'quick_wins':      [...skills learnable in < 2 weeks],
            'total_gaps':      5,
        }
        """
        logger.info(
            f"Analyzing {len(self.missing_skills)} skill gaps..."
        )

        # ── Analyze each missing skill ─────────────
        skill_gaps = []
        for i, skill in enumerate(self.missing_skills):
            gap = self._analyze_single_gap(skill, i + 1)
            skill_gaps.append(gap)

        # ── Sort by priority ───────────────────────
        skill_gaps.sort(key=lambda x: x['priority_score'],
                        reverse=True)

        # ── Re-number after sorting ────────────────
        for i, gap in enumerate(skill_gaps):
            gap['priority'] = i + 1

        # ── Split by importance ────────────────────
        critical  = [g for g in skill_gaps
                     if g['importance'] == 'Critical']
        important = [g for g in skill_gaps
                     if g['importance'] == 'Important']
        minor     = [g for g in skill_gaps
                     if g['importance'] == 'Nice to Have']

        # ── Calculate gap severity ─────────────────
        severity = self._calculate_severity(
            len(critical), len(important), len(minor)
        )

        # ── Calculate readiness score ──────────────
        readiness = self._calculate_readiness()

        # ── Generate action plan ───────────────────
        action_plan = self._generate_action_plan(skill_gaps)

        # ── Quick wins (learn in < 2 weeks) ────────
        quick_wins = [
            g for g in skill_gaps
            if g.get('is_quick_win', False)
        ]

        return {
            'skill_gaps':      skill_gaps,
            'critical_gaps':   [g['skill'] for g in critical],
            'important_gaps':  [g['skill'] for g in important],
            'minor_gaps':      [g['skill'] for g in minor],
            'critical_details':  critical,
            'important_details': important,
            'minor_details':     minor,
            'gap_severity':    severity,
            'readiness_score': readiness,
            'action_plan':     action_plan,
            'quick_wins':      quick_wins,
            'total_gaps':      len(self.missing_skills),
        }

    # ─────────────────────────────────────────────────
    # ANALYZE A SINGLE SKILL GAP
    # ─────────────────────────────────────────────────
    def _analyze_single_gap(self, skill, position):
        """
        Builds a complete analysis object for one
        missing skill.
        """
        skill_lower = skill.lower()

        # ── Get knowledge base entry ───────────────
        kb = self._get_knowledge(skill_lower)

        # ── Determine importance ───────────────────
        importance = self._determine_importance(skill)

        # ── Find related skills already owned ──────
        related_owned = self._find_related_owned(skill_lower, kb)

        # ── Adjust difficulty based on owned skills─
        difficulty = kb.get('difficulty', 'Medium')
        if related_owned:
            difficulty = self._adjust_difficulty(
                difficulty, len(related_owned)
            )

        # ── Calculate priority score ───────────────
        priority_score = self._calculate_priority_score(
            importance, difficulty
        )

        # ── Is it a quick win? ─────────────────────
        learn_time   = kb.get('learn_time', '2-4 weeks')
        is_quick_win = self._is_quick_win(learn_time)

        return {
            'skill':          skill,
            'importance':     importance,
            'importance_meta': self.IMPORTANCE_LEVELS.get(
                importance, {}
            ),
            'difficulty':     difficulty,
            'learn_time':     learn_time,
            'resources':      kb.get('resources', [
                f'Search: "{skill} tutorial for beginners"',
                f'YouTube: "{skill} crash course"',
                f'Udemy: "{skill} complete course"',
            ]),
            'tip':            kb.get('tip',
                f'Start with the official {skill} documentation '
                f'and build a small project.'),
            'related_owned':  related_owned,
            'priority_score': priority_score,
            'priority':       position,
            'is_quick_win':   is_quick_win,
        }

    # ─────────────────────────────────────────────────
    # DETERMINE IMPORTANCE OF A MISSING SKILL
    # ─────────────────────────────────────────────────
    def _determine_importance(self, skill):
        """
        Determines how important a missing skill is
        based on its position in JD requirements.
        """
        skill_lower      = skill.lower()
        required_lower   = [
            s.lower() for s in
            self.jd_data.get('required_skills', [])
        ]
        preferred_lower  = [
            s.lower() for s in
            self.jd_data.get('preferred_skills', [])
        ]
        jd_text_lower    = self.jd_data.get(
            'job_text', ''
        ).lower() if hasattr(self.jd_data, 'get') else ''

        if skill_lower in required_lower:
            # Check if it appears multiple times in JD
            # (signals higher importance)
            jd_text = str(self.jd_data)
            count   = jd_text.lower().count(skill_lower)
            if count >= 3:
                return 'Critical'
            return 'Critical'

        elif skill_lower in preferred_lower:
            return 'Important'

        else:
            return 'Nice to Have'

    # ─────────────────────────────────────────────────
    # FIND RELATED SKILLS ALREADY ON RESUME
    # ─────────────────────────────────────────────────
    def _find_related_owned(self, skill_lower, kb):
        """
        Finds skills the candidate already has that
        are related to the missing skill.

        Example: Missing 'PostgreSQL', has 'MySQL'
        → "Your MySQL knowledge transfers directly!"
        """
        related = kb.get('related', [])
        owned   = []

        for rel_skill in related:
            if rel_skill.lower() in self.all_resume:
                # Find proper case name
                for resume_skill in self.resume_skills.get(
                    'all_skills', []
                ):
                    if resume_skill.lower() == rel_skill.lower():
                        owned.append(resume_skill)
                        break
                else:
                    owned.append(rel_skill.title())

        return owned

    # ─────────────────────────────────────────────────
    # ADJUST DIFFICULTY BASED ON EXISTING KNOWLEDGE
    # ─────────────────────────────────────────────────
    def _adjust_difficulty(self, difficulty, related_count):
        """
        If candidate already knows related skills,
        the missing skill is easier to learn.
        """
        difficulty_order = ['Easy', 'Medium', 'Hard']

        idx = difficulty_order.index(difficulty) \
              if difficulty in difficulty_order else 1

        # Each related skill owned reduces difficulty by 1 level
        adjusted_idx = max(0, idx - min(related_count, 1))
        return difficulty_order[adjusted_idx]

    # ─────────────────────────────────────────────────
    # CALCULATE PRIORITY SCORE
    # ─────────────────────────────────────────────────
    def _calculate_priority_score(self, importance,
                                   difficulty):
        """
        Higher score = learn this first.

        Logic:
        - Critical skills always come first
        - Among same importance, easier skills come first
          (quick wins boost confidence)
        """
        importance_score = {
            'Critical':     100,
            'Important':     60,
            'Nice to Have':  20,
        }.get(importance, 50)

        # Easier skills get slight priority
        # (quick wins first for motivation)
        ease_bonus = {
            'Easy':   15,
            'Medium':  5,
            'Hard':    0,
        }.get(difficulty, 5)

        return importance_score + ease_bonus

    # ─────────────────────────────────────────────────
    # CALCULATE OVERALL SEVERITY
    # ─────────────────────────────────────────────────
    def _calculate_severity(self, critical_count,
                              important_count, minor_count):
        """
        Determines how severe the overall skill gap is.
        """
        if critical_count >= 3:
            return 'Critical'
        elif critical_count >= 1 or important_count >= 3:
            return 'Moderate'
        elif important_count >= 1 or minor_count >= 2:
            return 'Minor'
        else:
            return 'Minimal'

    # ─────────────────────────────────────────────────
    # CALCULATE READINESS SCORE
    # ─────────────────────────────────────────────────
    def _calculate_readiness(self):
        """
        How ready is the candidate for this role?
        Based on match result from semantic matcher.
        """
        overall = self.match_result.get('overall_match', 0)
        required = self.match_result.get('required_score', 0)

        # Weighted: 70% required match + 30% overall
        readiness = (required * 0.70 + overall * 0.30)
        return round(min(100, max(0, readiness)), 1)

    # ─────────────────────────────────────────────────
    # GENERATE ACTION PLAN
    # ─────────────────────────────────────────────────
    def _generate_action_plan(self, skill_gaps):
        """
        Creates a prioritized week-by-week action plan.
        """
        plan   = []
        week   = 1
        budget = 0   # time budget in weeks

        for gap in skill_gaps[:6]:  # Top 6 gaps only
            learn_time = gap.get('learn_time', '2-4 weeks')

            # Extract minimum weeks from learn_time string
            nums = [int(n) for n in
                    learn_time.replace('-', ' ').split()
                    if n.isdigit()]
            weeks_needed = min(nums) if nums else 2

            plan.append({
                'step':      len(plan) + 1,
                'skill':     gap['skill'],
                'start_week': week,
                'duration':  f"{learn_time}",
                'action':    f"Learn {gap['skill']} — "
                             f"{gap.get('tip', '')}",
                'resources': gap['resources'][:2],
                'importance': gap['importance'],
            })

            week   += weeks_needed
            budget += weeks_needed

        return plan

    # ─────────────────────────────────────────────────
    # HELPER: Is this a quick win?
    # ─────────────────────────────────────────────────
    def _is_quick_win(self, learn_time):
        """Skills learnable in ≤ 2 weeks = quick wins."""
        nums = [int(n) for n in
                learn_time.replace('-', ' ').split()
                if n.isdigit()]
        if not nums:
            return False
        return min(nums) <= 2

    # ─────────────────────────────────────────────────
    # HELPER: Get knowledge base entry
    # ─────────────────────────────────────────────────
    def _get_knowledge(self, skill_lower):
        """
        Gets knowledge base entry for a skill.
        Falls back to generic entry if skill not found.
        """
        # Direct lookup
        if skill_lower in self.SKILL_KNOWLEDGE:
            return self.SKILL_KNOWLEDGE[skill_lower]

        # Partial match
        for key, value in self.SKILL_KNOWLEDGE.items():
            if key in skill_lower or skill_lower in key:
                return value

        # Generic fallback
        return {
            'difficulty': 'Medium',
            'learn_time': '2-4 weeks',
            'resources': [
                f'Official {skill_lower.title()} documentation',
                f'YouTube: "{skill_lower} tutorial"',
                f'Udemy: "{skill_lower} bootcamp"',
            ],
            'related': [],
            'tip': (
                f'Start with the official {skill_lower.title()} '
                f'documentation and build a small project to '
                f'practice.'
            ),
        }


# ─────────────────────────────────────────────────────
# STANDALONE HELPER
# ─────────────────────────────────────────────────────
def analyze_skill_gaps(missing_skills, resume_skills,
                        jd_data, match_result=None):
    """
    Shortcut helper.

    Usage:
        from analyzer.services.gap_analyzer import analyze_skill_gaps
        result = analyze_skill_gaps(missing, resume_skills, jd_data)
    """
    analyzer = GapAnalyzer(
        missing_skills, resume_skills,
        jd_data, match_result
    )
    return analyzer.analyze()