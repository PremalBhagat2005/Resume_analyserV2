import re
import numpy as np
from app.utils.helpers import (
    check_action_verbs, score_action_verbs, extract_keywords, word_count,
    extract_email, extract_phone
)


def calculate_ats_score(resume_text: str, extracted_entities: dict) -> dict:
    """
    Calculate ATS score (0-100) based on multiple factors.
    
    Args:
        resume_text: Full resume text
        extracted_entities: Dictionary of extracted entities from NER
    
    Returns:
        dict: {
            'score': int (0-100),
            'breakdown': dict of individual scores,
            'extracted_keywords': list of keywords,
            'missing_sections': list of missing sections,
            'suggestions': list of improvement suggestions
        }
    """
    score = 0
    breakdown = {}
    suggestions = []
    
    # 1. Contact Information (20 points max)
    contact_score = 0
    missing_contact = []
    
    if extracted_entities.get('name'):
        contact_score += 7
    else:
        missing_contact.append('Name')
    
    if extracted_entities.get('email') or extract_email(resume_text):
        contact_score += 7
    else:
        missing_contact.append('Email')
    
    if extracted_entities.get('phone') or extract_phone(resume_text):
        contact_score += 6
    else:
        missing_contact.append('Phone')
    
    breakdown['contact_info'] = contact_score
    score += contact_score
    
    if missing_contact:
        suggestions.append(f"Add missing contact info: {', '.join(missing_contact)}")
    
    # 2. Skills Section (20 points)
    skills_score = 0
    if extracted_entities.get('skills') and len(extracted_entities['skills']) >= 3:
        skills_score = 20
    elif extracted_entities.get('skills') and len(extracted_entities['skills']) >= 1:
        skills_score = 10
    else:
        # Check for skills keywords in text
        skills_keywords = ['skills', 'competencies', 'technical', 'proficiency', 'expertise']
        if any(keyword in resume_text.lower() for keyword in skills_keywords):
            skills_score = 15
        else:
            suggestions.append("Add a dedicated Skills section with specific technical abilities")
    
    breakdown['skills_section'] = skills_score
    score += skills_score
    
    # 3. Education Section (15 points)
    education_score = 0
    education_keywords = ['education', 'degree', 'university', 'college', 'certification', 'bachelor', 'master']
    if any(keyword in resume_text.lower() for keyword in education_keywords):
        education_score = 15
    else:
        suggestions.append("Include an Education section with degree details")
    
    breakdown['education_section'] = education_score
    score += education_score
    
    # 4. Experience Section (15 points)
    experience_score = 0
    experience_keywords = ['experience', 'employment', 'worked', 'position', 'role', 'professional']
    if any(keyword in resume_text.lower() for keyword in experience_keywords):
        experience_score = 15
    else:
        suggestions.append("Add an Experience section with job history and responsibilities")
    
    breakdown['experience_section'] = experience_score
    score += experience_score
    
    # 5. Action Verbs and Keywords (20 points)
    verb_score = score_action_verbs(resume_text)
    keywords = extract_keywords(resume_text)
    
    if verb_score < 8:
        suggestions.append("Use more action verbs (e.g., managed, developed, implemented, led, engineered)")
    
    breakdown['action_verbs'] = verb_score
    score += verb_score
    
    # 6. Resume Length (10 points) - optimal 300-800 words
    word_count_value = word_count(resume_text)
    length_score = 0
    
    if 300 <= word_count_value <= 800:
        length_score = 10
    elif 200 <= word_count_value <= 900:
        length_score = 7
    elif word_count_value >= 100:
        length_score = 4
    else:
        suggestions.append("Resume is too short. Aim for 300-800 words")
    
    breakdown['resume_length'] = length_score
    score += length_score
    
    # Ensure score is within 0-100 range
    score = max(0, min(100, score))
    
    # Determine missing sections
    missing_sections = []
    if contact_score == 0:
        missing_sections.append("Complete Contact Information")
    if skills_score < 15:
        missing_sections.append("Skills Section")
    if education_score < 15:
        missing_sections.append("Education Section")
    if experience_score < 15:
        missing_sections.append("Experience Section")
    
    # Add general suggestions based on score
    if score < 50:
        suggestions.insert(0, "Your resume needs significant improvements for ATS optimization")
    elif score < 75:
        suggestions.insert(0, "Consider the suggestions below to improve your ATS score")
    else:
        suggestions.insert(0, "Your resume is well-optimized for ATS!")
    
    return {
        'score': score,
        'breakdown': breakdown,
        'extracted_keywords': keywords,
        'missing_sections': missing_sections,
        'suggestions': suggestions,
        'word_count': word_count_value
    }


def compute_ats_score_with_numpy(breakdown: dict) -> dict:
    """
    Compute ATS scores using NumPy for numerical operations.
    Provides the same output as calculate_ats_score but uses NumPy internally.
    
    Args:
        breakdown: Dictionary containing individual section scores
    
    Returns:
        dict: Same format as calculate_ats_score with numpy-computed metrics
    """
    # Define section scores and max points
    sections = np.array([
        breakdown.get('contact_info', 0),
        breakdown.get('skills_section', 0),
        breakdown.get('education_section', 0),
        breakdown.get('experience_section', 0),
        breakdown.get('action_verbs', 0),
        breakdown.get('resume_length', 0)
    ], dtype=np.float32)
    
    max_points = np.array([20, 20, 15, 15, 20, 10], dtype=np.float32)
    
    # Compute statistics using NumPy
    normalized_scores = (sections / max_points) * 100  # Normalize to 0-100
    total_score = float(np.sum(sections))
    mean_score = float(np.mean(normalized_scores))
    std_dev = float(np.std(normalized_scores))
    
    # Ensure score is within 0-100 range
    final_score = max(0, min(100, total_score))
    
    return {
        'score': final_score,
        'mean_normalized': mean_score,
        'std_dev': std_dev,
        'section_scores': sections.tolist(),
        'max_points': max_points.tolist(),
        'numpy_metrics': {
            'sum': float(np.sum(sections)),
            'mean': float(np.mean(sections)),
            'median': float(np.median(sections)),
            'max': float(np.max(sections)),
            'min': float(np.min(sections))
        }
    }

