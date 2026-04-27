import re
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_file(file):
    """
    Validate uploaded file for type and size.
    Returns (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is 5MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, None


def clean_text(text):
    """
    Clean and normalize text extracted from documents.
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:\'"@()\-#]', '', text)
    
    return text


KNOWN_SKILLS = {
    # ── Languages ─────────────────────────────────────────
    "python", "java", "javascript", "js", "typescript", "ts",
    "c", "c++", "cpp", "c#", "csharp", "r", "go", "golang",
    "rust", "bash", "shell", "scala", "kotlin", "swift",
    "php", "ruby", "matlab", "dart", "perl", "elixir",
    "haskell", "lua", "groovy", "fortran", "cobol",

    # ── Web Frontend ───────────────────────────────────────
    "html", "css", "sass", "scss", "less",
    "react", "reactjs", "react.js",
    "next.js", "nextjs", "next",
    "vue", "vuejs", "vue.js",
    "angular", "angularjs",
    "svelte", "astro",
    "tailwind", "tailwindcss", "tailwind css",
    "bootstrap", "material ui", "chakra ui",
    "jquery", "webpack", "vite", "parcel", "babel",
    "redux", "zustand", "mobx",

    # ── Web Backend ────────────────────────────────────────
    "node", "nodejs", "node.js",
    "express", "expressjs", "express.js",
    "flask", "django", "fastapi",
    "spring", "spring boot", "springboot",
    "laravel", "rails", "ruby on rails",
    "nestjs", "nest.js",
    "graphql", "rest", "restful", "api", "grpc",
    "websocket", "socket.io",

    # ── Databases ──────────────────────────────────────────
    "sql", "mysql", "postgresql", "postgres",
    "sqlite", "oracle", "mssql", "sql server",
    "mongodb", "mongo", "mongoose",
    "redis", "memcached",
    "elasticsearch", "opensearch",
    "dynamodb", "firestore", "firebase",
    "cassandra", "couchdb", "neo4j",
    "supabase", "planetscale", "neon",

    # ── Cloud & DevOps ─────────────────────────────────────
    "aws", "amazon web services",
    "gcp", "google cloud", "google cloud platform",
    "azure", "microsoft azure",
    "vercel", "netlify", "heroku", "render",
    "docker", "dockerfile", "containerization",
    "kubernetes", "k8s",
    "terraform", "ansible", "puppet", "chef",
    "ci/cd", "github actions", "gitlab ci",
    "jenkins", "circleci", "travis ci",
    "nginx", "apache", "caddy",
    "linux", "ubuntu", "debian", "centos",
    "oracle cloud infrastructure",

    # ── Version Control ────────────────────────────────────
    "git", "github", "gitlab", "bitbucket",
    "svn", "mercurial",

    # ── Data Science / ML / AI ─────────────────────────────
    "numpy", "pandas", "matplotlib", "seaborn", "plotly",
    "scikit-learn", "sklearn",
    "tensorflow", "tf", "keras",
    "pytorch", "torch",
    "opencv", "cv2",
    "nltk", "spacy", "gensim", "transformers",
    "huggingface", "hugging face",
    "langchain", "llamaindex",
    "machine learning", "ml",
    "deep learning", "dl",
    "nlp", "natural language processing",
    "computer vision", "cv",
    "data science", "data analysis", "data engineering",
    "artificial intelligence", "ai",
    "generative ai", "gen ai", "llm",
    "reinforcement learning",
    "xgboost", "lightgbm", "catboost",
    "jupyter", "google colab", "colab",

    # ── Tools & Platforms ──────────────────────────────────
    "figma", "sketch", "adobe xd",
    "vs code", "vscode", "visual studio",
    "intellij", "pycharm", "webstorm",
    "postman", "insomnia", "swagger",
    "jira", "confluence", "notion",
    "slack", "trello", "asana",
    "microsoft excel", "excel",
    "powerpoint", "word",
    "linux terminal", "ubuntu",
    "android studio", "xcode",

    # ── Mobile ─────────────────────────────────────────────
    "react native", "flutter", "ionic",
    "android", "ios", "swift", "kotlin",

    # ── Blockchain / Web3 ──────────────────────────────────
    "solidity", "web3", "web3.js", "ethers.js",
    "blockchain", "smart contracts",

    # ── Testing ────────────────────────────────────────────
    "jest", "mocha", "chai", "cypress",
    "pytest", "unittest", "selenium",
    "playwright", "puppeteer",

    # ── Soft Skills ────────────────────────────────────────
    "leadership", "communication", "teamwork",
    "team collaboration", "problem solving",
    "adaptability", "agile", "scrum", "kanban",
    "time management", "critical thinking",
    "public speaking", "project management",
}

NOISE_WORDS = {
    # Months
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
    "january", "february", "march", "april", "june",
    "july", "august", "september", "october", "november", "december",
    # Filler
    "remote", "intern", "summary", "aspiring", "certified", "introduction",
    "bachelor", "master", "participant", "skilled", "program", "tools", "demo",
    "video", "crash", "course", "word", "soft", "west", "bengal", "iit", "rae",
    "collaboratedwith", "reached", "highest", "milestone", "spearheadedcross",
    # Single chars
    "a", "i", "the", "and", "or", "of", "in", "to", "for", "with", "on", "at", "by",
}


def extract_skills_from_keywords(keywords: list) -> list:
    """
    Match raw NER keywords against KNOWN_SKILLS.
    Handles: exact match, lowercase, partial containment.
    """
    skills = []
    for kw in keywords:
        kw_clean = kw.strip()
        kw_lower = kw_clean.lower()

        # 1. Exact lowercase match
        if kw_lower in KNOWN_SKILLS:
            skills.append(kw_clean)
            continue

        # 2. Check if any known skill is fully contained
        #    in the keyword or vice versa (handles "Node.js" -> "node")
        matched = False
        for known in KNOWN_SKILLS:
            if len(known) >= 2 and (
                known in kw_lower or
                kw_lower in known
            ):
                skills.append(kw_clean)
                matched = True
                break

    # Deduplicate preserving order, normalise to title case
    seen = set()
    result = []
    for s in skills:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            result.append(s)

    return sorted(result, key=lambda x: x.lower())


def clean_keywords(keywords: list) -> list:
    """Remove noise words, month names, overly long phrases from keyword list."""
    cleaned = []
    for kw in keywords:
        kw_clean = kw.strip()
        # Skip if in noise list
        if kw_clean.lower() in NOISE_WORDS:
            continue
        # Skip if too long (more than 4 words = likely a sentence fragment)
        if len(kw_clean.split()) > 4:
            continue
        # Skip if too short
        if len(kw_clean) <= 2:
            continue
        # Skip if contains digits that look like years/dates
        if re.search(r'\b(19|20)\d{2}\b', kw_clean):
            continue
        # Skip if looks like a concatenated word (e.g. "Collaboratedwith")
        if re.search(r'[a-z][A-Z]', kw_clean):
            continue
        cleaned.append(kw_clean)
    return list(dict.fromkeys(cleaned))  # deduplicate preserving order


def extract_email(text):
    """
    Extract email address from text.
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None


def extract_phone(text):
    """
    Extract phone number from text.
    """
    phone_pattern = r'(?:\+\d{1,3})?[\s.-]?\(?(?:\d{3}|\d{4})\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else None


ACTION_VERBS = [
    "managed", "developed", "designed", "implemented", "led", "built",
    "created", "improved", "optimized", "analyzed", "collaborated",
    "delivered", "achieved", "engineered", "deployed", "integrated",
    "automated", "mentored", "coordinated", "researched", "launched",
    "reduced", "increased", "streamlined", "spearheaded", "established",
]

def check_action_verbs(text):
    """
    Check for presence of action verbs in text.
    Returns count of unique action verbs found.
    """
    text_lower = text.lower()
    found = [v for v in ACTION_VERBS if v in text_lower]
    return len(set(found))

def score_action_verbs(text: str) -> int:
    """
    Score 0–20 based on how many unique action verbs appear in resume.
    0 verbs = 0pts, 1-2 = 8pts, 3-5 = 14pts, 6+ = 20pts
    """
    text_lower = text.lower()
    found = [v for v in ACTION_VERBS if v in text_lower]
    count = len(set(found))
    if count == 0:
        return 0
    elif count <= 2:
        return 8
    elif count <= 5:
        return 14
    else:
        return 20


def extract_keywords(text):
    """
    Extract keywords from resume text based on common patterns.
    """
    keywords = []
    
    # Extract skills-like words (capitalized words and abbreviations)
    skill_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2,})\b'
    potential_skills = re.findall(skill_pattern, text)
    
    # Filter common words
    common_words = {'The', 'A', 'An', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For', 'Of', 'With'}
    keywords = [skill for skill in potential_skills if skill not in common_words]
    
    # Remove duplicates and limit
    keywords = list(set(keywords))[:50]
    
    return keywords


def word_count(text):
    """
    Count words in text.
    """
    return len(text.split())
