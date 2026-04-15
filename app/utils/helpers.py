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
    # Languages
    "python", "java", "javascript", "c++", "c#", "sql", "r", "go", "rust",
    "typescript", "kotlin", "swift", "php", "ruby", "scala", "bash",
    # Web
    "html", "css", "react", "node", "node.js", "flask", "django", "fastapi",
    "express", "vue", "angular", "rest", "api", "graphql",
    # Cloud & DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "git", "github", "ci/cd",
    "google cloud platform", "oracle cloud infrastructure", "vercel",
    # AI/ML
    "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
    "scikit-learn", "artificial intelligence", "generative", "llm",
    # Tools
    "figma", "microsoft excel", "postman", "linux", "mongodb", "postgresql",
    "mysql", "firebase", "redis",
    # Soft skills
    "leadership", "communication", "agile", "scrum",
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
    """Filter raw NER keywords down to recognised tech/professional skills."""
    skills = []
    for kw in keywords:
        if kw.lower().strip() in KNOWN_SKILLS:
            skills.append(kw)
    return sorted(set(skills))


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
