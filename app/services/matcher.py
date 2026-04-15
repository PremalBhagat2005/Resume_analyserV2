import re
from app.services.hf_client import get_job_match


def extract_job_keywords(job_description: str) -> dict:
    """
    Extract key information from job description.
    
    Args:
        job_description: Job description text
    
    Returns:
        dict: Extracted keywords, skills, and requirements
    """
    # Extract technical skills (capitalized words and acronyms)
    skill_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2,})\b'
    skills = list(set(re.findall(skill_pattern, job_description)))
    
    # Extract common job requirements
    requirements = []
    requirement_patterns = {
        'years_of_experience': r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience',
        'education': r'(?:bachelor|master|phd|degree|diploma)',
        'certifications': r'(?:certified|certification|acm|aws|azure|gcp)',
    }
    
    for req_type, pattern in requirement_patterns.items():
        if re.search(pattern, job_description, re.IGNORECASE):
            requirements.append(req_type)
    
    return {
        'skills': skills[:30],
        'requirements': requirements
    }


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
    # Get similarity score from HF API
    similarity_data = get_job_match(resume_text, job_description)
    match_score = similarity_data['match_score']
    
    # Get matched and missing keywords
    matched_keywords = similarity_data['matched_keywords'][:10]
    missing_keywords = similarity_data['missing_keywords'][:10]
    
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
        'feedback': feedback
    }
