import re
from concurrent.futures import ThreadPoolExecutor

from app.services.hf_client import (
    extract_skills_fallback as extract_skills_from_text,
    get_semantic_similarity,
    get_section_similarities,
    get_requirement_coverage,
)

STOPWORDS = {
    # Articles, prepositions, conjunctions
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'between', 'out', 'off', 'over', 'under', 'again', 'then',
    'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both', 'each',
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not', 'only', 'own',
    'same', 'so', 'than', 'too', 'very', 'just', 'because', 'as', 'until', 'while',
    'its', 'it', 'this', 'that', 'these', 'those', 'they', 'them', 'their', 'our',
    'your', 'his', 'her', 'my', 'we', 'us', 'you', 'he', 'she', 'i', 'me', 'him',
    # Auxiliary verbs
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'must', 'shall', 'can', 'need', 'ought',
    # Common action verbs (not skills)
    'deliver', 'delivering', 'delivered', 'apply', 'applying', 'applied',
    'work', 'working', 'worked', 'lead', 'leading', 'led', 'create', 'creating',
    'use', 'using', 'used', 'make', 'making', 'made', 'take', 'taking', 'took',
    'get', 'getting', 'got', 'give', 'giving', 'gave', 'come', 'coming', 'came',
    'see', 'seeing', 'saw', 'know', 'knowing', 'think', 'thinking', 'thought',
    'look', 'looking', 'want', 'wanting', 'include', 'including', 'ensure',
    'ensuring', 'seek', 'seeking', 'require', 'requiring', 'provide',
    'providing', 'meet', 'meeting', 'met', 'build', 'building', 'built',
    'support', 'supporting', 'supported', 'manage', 'managing', 'managed',
    'develop', 'developing', 'developed', 'design', 'designing', 'designed',
    'implement', 'implementing', 'implemented', 'maintain', 'maintaining',
    'improve', 'improving', 'improved', 'present', 'presenting', 'presented',
    'collaborate', 'collaborating', 'collaborated', 'communicate',
    'learn', 'learning', 'learned', 'adapt', 'adapting', 'adapted',
    'demonstrate', 'demonstrating', 'demonstrated',
    # Common adjectives (not skills)
    'new', 'good', 'great', 'large', 'small', 'high', 'low', 'long', 'short',
    'clear', 'clearly', 'strong', 'key', 'core', 'main', 'full', 'free',
    'global', 'local', 'general', 'specific', 'multiple', 'various',
    'advanced', 'complex', 'complexity', 'simple', 'confident', 'confidently',
    'excellent', 'exceptional', 'minimum', 'maximum', 'minimal', 'positive',
    'technical', 'creative', 'innovative', 'strategic', 'effective',
    'efficient', 'professional', 'international', 'digital', 'visual',
    'relevant', 'required', 'preferred', 'bonus', 'ideal', 'proven',
    # Common nouns (not skills)
    'team', 'teams', 'role', 'roles', 'job', 'task', 'tasks', 'project',
    'projects', 'product', 'products', 'client', 'clients', 'company',
    'brand', 'brands', 'business', 'value', 'values', 'insight', 'insights',
    'result', 'results', 'impact', 'standard', 'standards', 'process',
    'system', 'systems', 'platform', 'platforms', 'solution', 'solutions',
    'service', 'services', 'opportunity', 'experience', 'requirement',
    'requirements', 'candidate', 'portfolio', 'application', 'position',
    'level', 'type', 'way', 'day', 'week', 'year', 'time', 'part', 'people',
    'person', 'world', 'industry', 'environment', 'culture', 'community',
    'history', 'future', 'example', 'examples', 'description', 'information',
    'ability', 'skills', 'skill', 'knowledge', 'understanding', 'approach',
    # Filler words
    'please', 'least', 'well', 'also', 'either', 'whether',
    'within', 'without', 'across', 'around', 'along', 'against', 'behind',
    'beside', 'beyond', 'despite', 'except', 'since', 'though', 'although',
    'however', 'therefore', 'thus', 'hence', 'whereas', 'what', 'which',
    'who', 'whom', 'whose', 'if', 'unless', 'following', 'regarding',
    'per', 'via', 'vs', 'etc', 'eg', 'ie', 're'
}


def extract_meaningful_keywords(text: str) -> set[str]:
    """
    Extract only meaningful keywords from text.
    Filters out stopwords, punctuation, short tokens, numbers, month names.
    Works generically on any text - no hardcoded domain assumptions.
    """
    months = {
        'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
        'january', 'february', 'march', 'april', 'june', 'july', 'august', 'september',
        'october', 'november', 'december'
    }

    tokens = re.split(r"[\s,;:()\[\]{}<>/\\|@#$%^&*+=~`\"'!?]+", text)

    keywords: set[str] = set()
    for token in tokens:
        token = re.sub(r'^[^\w]+|[^\w]+$', '', token)
        token = token.strip().lower()

        if not token:
            continue
        if len(token) < 3:
            continue
        if token.isdigit():
            continue
        if re.match(r'^\d+[\w]*$', token) and token[:2].isdigit():
            continue
        if token in months:
            continue
        if token in STOPWORDS:
            continue
        if not token[0].isalpha():
            continue

        keywords.add(token)

    return keywords


def extract_jd_keywords(job_description: str) -> list[str]:
    """Backward-compatible helper that returns cleaned JD keywords as a list."""
    return sorted(list(extract_meaningful_keywords(job_description)))


def extract_job_keywords(job_description: str) -> dict:
    """
    Extract key information from job description.
    
    Args:
        job_description: Job description text
    
    Returns:
        dict: Extracted keywords, skills, and requirements
    """
    skills = sorted(list(extract_meaningful_keywords(job_description)))[:30]

    requirements = []
    if re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience', job_description, re.IGNORECASE):
        requirements.append('years_of_experience')
    if re.search(r'(?:bachelor|master|phd|degree|diploma)', job_description, re.IGNORECASE):
        requirements.append('education')
    if re.search(r'(?:certified|certification)', job_description, re.IGNORECASE):
        requirements.append('certifications')

    return {
        'skills': skills[:30],
        'requirements': requirements
    }


def match_job_description(resume_text: str, job_description: str) -> dict:
    """Compute a hybrid keyword + semantic match with section and requirement insights."""
    jd_skills = set()
    try:
        jd_skills = set(extract_meaningful_keywords(job_description))
    except Exception as e:
        print(f"[Matcher] JD keyword extraction failed: {e}")

    resume_skills = set()
    try:
        resume_skills = set(extract_skills_from_text(resume_text))
    except Exception as e:
        print(f"[Matcher] Resume skill fallback failed: {e}")

    if not jd_skills or not resume_skills:
        try:
            jd_skills = set(extract_meaningful_keywords(job_description))
            resume_skills = set(extract_meaningful_keywords(resume_text))
        except Exception as e:
            print(f"[Matcher] Keyword fallback failed: {e}")

    resume_lower = {s.lower().strip() for s in resume_skills if str(s).strip()}
    jd_lower = {s.lower().strip() for s in jd_skills if str(s).strip()}

    exact_matches = resume_lower & jd_lower
    matched = sorted(list(exact_matches))[:15]

    missing = []
    for term in sorted(list(jd_lower - resume_lower))[:8]:
        try:
            near_match = get_semantic_similarity(resume_text, term)
            if near_match is not None and near_match >= 0.55:
                matched.append(term)
                continue
        except Exception as e:
            print(f"[Matcher] Semantic dedupe failed for '{term}': {e}")
        missing.append(term)

    matched = sorted(list(dict.fromkeys(matched)))[:15]
    missing = missing[:15]

    keyword_score = 0
    if len(jd_lower) > 0:
        keyword_score = round((len(exact_matches) / len(jd_lower)) * 100)

    # Run semantic analysis, section scoring, and requirement coverage in parallel
    semantic_score = None
    section_scores = {}
    requirement_coverage = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Task 1: Get semantic similarity score
        semantic_future = executor.submit(
            get_semantic_similarity, 
            resume_text, 
            job_description
        )
        
        # Task 2: Get section similarities
        sections = {}
        summary_text = ""
        if isinstance(resume_text, str):
            summary_text = resume_text[:500]
        if summary_text:
            sections['Summary'] = summary_text
        if resume_skills:
            sections['Skills'] = ' '.join(sorted(list(resume_skills)))
        if resume_text:
            sections['Experience'] = resume_text
        
        sections_future = executor.submit(
            get_section_similarities,
            sections if sections else None,
            job_description
        )
        
        # Task 3: Get requirement coverage
        requirements_future = executor.submit(
            _get_jd_requirements_and_coverage,
            job_description,
            resume_text
        )
        
        # Collect results as they complete
        try:
            raw = semantic_future.result(timeout=90)
            if raw is not None:
                semantic_score = round(raw * 100)
                print(f"[Matcher] Semantic score: {semantic_score}")
        except Exception as e:
            print(f"[Matcher] Semantic score failed: {e}")
        
        try:
            section_scores = sections_future.result(timeout=60)
            if section_scores:
                print(f"[Matcher] Section scores: {section_scores}")
        except Exception as e:
            print(f"[Matcher] Section similarity failed: {e}")
        
        try:
            requirement_coverage = requirements_future.result(timeout=60)
            if requirement_coverage:
                print(f"[Matcher] Requirement coverage computed for {len(requirement_coverage)} items")
        except Exception as e:
            print(f"[Matcher] Requirement coverage failed: {e}")

    if semantic_score is not None:
        final_score = round(0.6 * keyword_score + 0.4 * semantic_score)
    else:
        final_score = keyword_score

    raw_boost = min(len(missing), 20)
    projected = min(100, final_score + raw_boost)
    actual_boost = projected - final_score

    return {
        'match_score': final_score,
        'keyword_score': keyword_score,
        'semantic_score': semantic_score,
        'matched_keywords': matched,
        'missing_keywords': missing,
        'section_scores': section_scores,
        'requirement_coverage': requirement_coverage,
        'score_projection': {
            'current': final_score,
            'projected': projected,
            'boost': actual_boost,
        }
    }


def _get_jd_requirements_and_coverage(job_description: str, resume_text: str) -> list:
    """Helper function to extract JD requirements and compute coverage."""
    lines = re.split(r'\n|•|\*|(?<=\.)(?=\s[A-Z])', job_description)
    jd_requirements = [
        l.strip() for l in lines
        if 25 <= len(l.strip()) <= 300
    ][:6]
    
    requirement_coverage = []
    if jd_requirements:
        requirement_coverage = get_requirement_coverage(jd_requirements, resume_text)
    
    return requirement_coverage


def match_resume_to_job(resume_text: str, job_description: str) -> dict:
    """
    Match resume against job description and provide detailed feedback.
    
    Args:
        resume_text: Resume text
        job_description: Job description text
    
    Returns:
        dict: {
            'match_score': int (0-100),
            'matched_keywords': list[str],
            'missing_keywords': list[str],
            'feedback': str
        }
    """
    match_data = match_job_description(resume_text, job_description)
    match_score = match_data['match_score']
    matched_keywords = match_data['matched_keywords']
    missing_keywords = match_data['missing_keywords']
    
    # Generate feedback based on score
    if match_score >= 80:
        feedback = "Excellent match! Your resume aligns well with this role."
    elif match_score >= 60:
        feedback = "Good match. Consider adding more role-specific keywords."
    elif match_score >= 40:
        feedback = "Moderate match. Tailor your resume further to this job."
    else:
        feedback = "Low match. Significant gaps between resume and job requirements."
    
    return {
        'match_score': match_score,
        'matched_keywords': matched_keywords,
        'missing_keywords': missing_keywords,
        'feedback': feedback,
        'score_projection': match_data['score_projection']
    }
