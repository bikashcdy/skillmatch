"""Skill vocabulary, relationships and education levels used by the matching engine."""

# canonical skill -> aliases. Extend this dictionary (or load it from the DB) as you grow.
SKILLS = {
    # --- programming & web ---
    "python": ["python", "py"],
    "django": ["django", "drf", "django rest framework"],
    "flask": ["flask"],
    "javascript": ["javascript", "js", "es6"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "reactjs", "react.js"],
    "react native": ["react native"],
    "next.js": ["next.js", "nextjs"],
    "vue": ["vue", "vuejs", "vue.js"],
    "angular": ["angular", "angularjs"],
    "node.js": ["node", "nodejs", "node.js", "express.js", "expressjs"],
    "html": ["html", "html5"],
    "css": ["css", "css3", "tailwind", "bootstrap", "sass"],
    "php": ["php"],
    "laravel": ["laravel"],
    "wordpress": ["wordpress", "woocommerce"],
    "java": ["java"],
    "spring boot": ["spring boot", "springboot"],
    "c#": ["c#", "asp.net", ".net", "dotnet"],
    "c++": ["c++", "cpp"],
    "flutter": ["flutter", "dart"],
    "android": ["android", "kotlin"],
    "ios": ["ios", "swiftui", "ios development"],
    "rest api": ["rest", "rest api", "restful", "api development"],
    # --- data & cloud ---
    "sql": ["sql", "mysql", "postgresql", "postgres", "sqlite"],
    "mongodb": ["mongodb", "mongo"],
    "firebase": ["firebase", "firestore"],
    "git": ["git", "github", "gitlab"],
    "docker": ["docker", "containers"],
    "devops": ["devops", "ci/cd", "jenkins", "kubernetes", "github actions"],
    "aws": ["aws", "amazon web services"],
    "linux": ["linux", "ubuntu", "bash", "shell scripting"],
    "networking": ["networking", "ccna", "cisco", "tcp/ip", "mikrotik"],
    "cybersecurity": ["cybersecurity", "cyber security", "ethical hacking", "penetration testing"],
    "machine learning": ["machine learning", "ml", "scikit-learn", "sklearn", "deep learning", "tensorflow", "pytorch", "nlp"],
    "data analysis": ["data analysis", "pandas", "numpy", "excel", "ms excel", "power bi", "tableau"],
    "testing": ["testing", "qa", "quality assurance", "selenium", "pytest", "unit testing"],
    # --- design & media ---
    "ui/ux design": ["ui/ux", "ux design", "ui design", "wireframing", "prototyping"],
    "figma": ["figma", "adobe xd"],
    "graphic design": ["graphic design", "photoshop", "illustrator", "canva", "coreldraw"],
    "video editing": ["video editing", "premiere pro", "after effects", "capcut"],
    # --- business & office (common in Nepal) ---
    "digital marketing": ["digital marketing", "seo", "social media marketing", "google ads", "facebook ads", "content marketing", "email marketing"],
    "content writing": ["content writing", "copywriting", "blogging"],
    "accounting": ["accounting", "tally", "bookkeeping", "quickbooks", "taxation", "vat"],
    "sales": ["sales", "business development", "lead generation"],
    "customer service": ["customer service", "customer support", "call center"],
    "project management": ["project management", "scrum", "agile", "jira", "kanban"],
    "ms office": ["ms office", "microsoft office", "ms word", "powerpoint"],
    "human resources": ["human resources", "recruitment", "payroll"],
    "communication": ["communication", "teamwork", "leadership"],
}

# Knowing the left skill implies the right one (a Django developer knows Python).
IMPLIES = {
    "django": ["python"], "flask": ["python"], "react": ["javascript"], "next.js": ["react", "javascript"],
    "vue": ["javascript"], "angular": ["javascript", "typescript"], "node.js": ["javascript"],
    "typescript": ["javascript"], "react native": ["react", "javascript"], "laravel": ["php"],
    "wordpress": ["php"], "spring boot": ["java"], "figma": ["ui/ux design"],
    "devops": ["linux"], "machine learning": ["python"],
}


# Education levels (numeric) used by the education scorer.
EDUCATION_LEVELS = {
    "none": 0,
    "secondary": 1,
    "diploma": 2,  # Higher secondary / +2 / diploma
    "higher secondary": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
    "doctorate": 5,
}
EDUCATION_NAMES = {0: "none", 1: "secondary", 2: "diploma / +2", 3: "bachelor", 4: "master", 5: "doctorate"}
EDUCATION_KEYWORDS = {
    "phd": ["phd", "ph.d", "doctorate"],
    "master": ["master", "msc", "m.sc", "mca", "mba", "m.tech"],
    "bachelor": ["bachelor", "bsc", "b.sc", "bca", "bba", "b.tech", "b.e.", "undergraduate"],
    "diploma": ["diploma", "+2", "higher secondary", "a-level", "plus two", "10+2"],
    "secondary": ["slc", "s.l.c", "secondary school", "high school"],
}

# Skills in the same group are "related": a candidate who knows one earns 0.5 for another.
SKILL_GROUPS = {
    "web frontend": ["react", "vue", "angular", "next.js", "javascript", "typescript"],
    "python web": ["django", "flask"],
    "php web": ["php", "laravel", "wordpress"],
    "backend languages": ["python", "java", "c#", "c++", "node.js", "php"],
    "mobile": ["flutter", "android", "ios", "react native"],
    "databases": ["sql", "mongodb", "firebase"],
    "cloud and devops": ["docker", "devops", "aws", "linux"],
    "data and ai": ["machine learning", "data analysis"],
    "design": ["ui/ux design", "figma", "graphic design", "video editing"],
    "marketing": ["digital marketing", "content writing", "sales", "customer service"],
    "business office": ["accounting", "ms office", "human resources", "project management"],
    "security and network": ["networking", "cybersecurity"],
}

# skill -> skills that should be learned first. Used to order the learning path.
PREREQUISITES = {
    "css": ["html"],
    "javascript": ["html", "css"],
    "typescript": ["javascript"],
    "react": ["javascript"],
    "vue": ["javascript"],
    "angular": ["typescript"],
    "next.js": ["react"],
    "react native": ["react"],
    "node.js": ["javascript"],
    "django": ["python"],
    "flask": ["python"],
    "machine learning": ["python", "data analysis"],
    "data analysis": ["python"],
    "spring boot": ["java"],
    "laravel": ["php"],
    "wordpress": ["html", "css"],
    "docker": ["linux"],
    "devops": ["docker", "git", "linux"],
    "aws": ["linux"],
    "cybersecurity": ["networking", "linux"],
    "rest api": ["python"],
}

# canonical name and every alias -> canonical name (the synonym dictionary)
ALIAS_INDEX = {}
for _skill, _aliases in SKILLS.items():
    ALIAS_INDEX[_skill] = _skill
    for _a in _aliases:
        ALIAS_INDEX.setdefault(_a, _skill)
