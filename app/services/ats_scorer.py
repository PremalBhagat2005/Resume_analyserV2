import re
from app.utils.helpers import extract_keywords, word_count, ACTION_VERBS, KNOWN_SKILLS, DEGREE_KEYWORDS, INSTITUTION_KEYWORDS

# Define the exact max points for each ATS section to avoid hardcoding
ATS_MAX_POINTS = {
    "contact_info": 20,
    "skills_section": 20,
    "education_section": 15,
    "experience_section": 15,
    "action_verbs_keywords": 20,
    "resume_length": 10
}



def calculate_ats_score(resume_text: str, entities: dict = None) -> dict:
    """
    Calculate ATS score (0-100) based on multiple factors.
    
    Args:
        resume_text: Full resume text
        entities: Dictionary of extracted entities from NER/extractors
    
    Returns:
        dict: {
            'score': int (0-100),
            'breakdown': dict of individual scores,
            'extracted_keywords': list of keywords,
            'missing_sections': list of missing sections,
            'suggestions': list of improvement suggestions
        }
    """
    if entities is None:
        entities = {}

    score = 0
    breakdown = {}
    suggestions = []
    
    # 1. Contact Information (20 points max) - use extracted entities only
    contact_score = 0
    name = entities.get('name', 'Not detected')
    email = entities.get('email', 'Not detected')
    phone = entities.get('phone', 'Not detected')
    
    has_name = bool(name) and str(name).lower() != 'not detected'
    has_email = bool(email) and str(email).lower() != 'not detected'
    has_phone = bool(phone) and str(phone).lower() != 'not detected'
    
    # Check if name matches email prefix (should NOT award name points)
    name_matches_email_prefix = False
    if has_name and has_email and '@' in email:
        email_local = email.split('@')[0].lower()
        name_lower = name.lower()
        # If name is just the email prefix, don't give points
        if email_local in name_lower or name_lower in email_local:
            name_matches_email_prefix = True
    
    if has_name and not name_matches_email_prefix:
        contact_score += 7
    
    if has_email:
        contact_score += 7
    
    if has_phone:
        contact_score += 6
    
    breakdown['contact_info'] = contact_score
    score += contact_score
    
    # 2. Skills Section (20 points) - STRICTER
    skills_score = 0
    
    # Accept these section header variants (case-insensitive)
    valid_skills_headers = {
        'skills', 'core skills', 'technical skills', 'key skills', 'skill set',
        'competencies', 'technologies', 'tech stack'
    }
    
    # Check if resume has a valid skills section header
    has_valid_skills_header = any(
        header.lower() in resume_text.lower() 
        for header in valid_skills_headers
    )
    
    skills_list = entities.get('skills', [])
    skill_count = len(skills_list) if skills_list else 0
    
    if has_valid_skills_header:
        skills_score += 8
    
    if skill_count >= 3:
        skills_score += 7
    if skill_count >= 6:
        skills_score += 5  # Bonus for 6+ skills
    
    skills_score = min(20, skills_score)
    breakdown['skills_section'] = skills_score
    score += skills_score
    
    # 3. Education Section (15 points) - broadened detection
    education_score = 0

    edu_text = resume_text.lower()

    degree_keywords = list(DEGREE_KEYWORDS)
    institution_keywords = list(INSTITUTION_KEYWORDS)

    edu_headers = ['education', 'academic', 'qualification', 'scholastic']

    has_edu_section = any(h in edu_text for h in edu_headers)
    has_degree = any(kw in edu_text for kw in degree_keywords)
    has_institution = any(kw in edu_text for kw in institution_keywords)

    in_progress_markers = ['present', 'pursuing', 'ongoing', 'current', 'expected']
    is_in_progress = any(m in edu_text for m in in_progress_markers)

    if has_edu_section and has_degree and has_institution:
        if is_in_progress:
            education_score = 11
        else:
            education_score = 15
    elif has_degree and has_institution:
        education_score = 10
    elif has_edu_section and (has_degree or has_institution):
        education_score = 8
    elif has_degree or has_institution:
        education_score = 5
    else:
        education_score = 0

    breakdown['education_section'] = education_score
    score += education_score

    # 4. Experience Section (15 points) - use extracted entities first
    experience_score = 0

    experience_list = entities.get('experience', [])
    if not isinstance(experience_list, list):
        experience_list = []
    experience_list = [
        e for e in experience_list
        if e and "no work experience detected" not in str(e).lower() and str(e).lower() != "not detected"
    ]

    exp_keywords = [
        'work experience', 'experience', 'employment', 'internship',
        'internships', 'work history', 'professional experience', 'position'
    ]
    has_exp_section = any(kw in resume_text.lower() for kw in exp_keywords)

    date_pattern = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w\s,.\-–—]{0,30}\d{4}'
    has_dates = bool(re.search(date_pattern, resume_text, re.IGNORECASE))

    if experience_list and len(experience_list) > 0:
        experience_score += 6
        if len(experience_list) >= 2:
            experience_score += 5
        if has_dates:
            experience_score += 4
    elif has_exp_section:
        experience_score += 6
        if has_dates:
            experience_score += 5
    
    experience_score = min(15, experience_score)
    breakdown['experience_section'] = experience_score
    score += experience_score
    
    # 5. Action Verbs and Keywords (20 points) - MUCH STRICTER
    keywords = extract_keywords(resume_text)
    
    action_verbs_list = list(ACTION_VERBS)
    
    tech_keywords_list = list(KNOWN_SKILLS)
    
    text_lower = resume_text.lower()
    action_verbs_count = sum(1 for verb in action_verbs_list if verb in text_lower)
    tech_keywords_count = sum(1 for keyword in tech_keywords_list if keyword in text_lower)
    
    keywords_score = 0
    if action_verbs_count >= 5 and tech_keywords_count >= 8:
        keywords_score = 20
    elif (action_verbs_count >= 3 and action_verbs_count <= 4) or (tech_keywords_count >= 5 and tech_keywords_count <= 7):
        keywords_score = 14
    elif (action_verbs_count >= 1 and action_verbs_count <= 2) or (tech_keywords_count >= 3 and tech_keywords_count <= 4):
        keywords_score = 8
    else:
        keywords_score = 0
    
    breakdown['action_verbs_keywords'] = keywords_score
    score += keywords_score
    
    # 6. Resume Length (10 points) - optimal 300-800 words
    word_count_value = word_count(resume_text)
    length_score = 0
    
    if 300 <= word_count_value <= 800:
        length_score = 10
    elif 200 <= word_count_value <= 900:
        length_score = 7
    elif word_count_value >= 100:
        length_score = 4
    
    breakdown['resume_length'] = length_score
    score += length_score
    
    total_score = contact_score + skills_score + education_score + experience_score + keywords_score + length_score

    # Suggestions: generated from computed scores only
    if contact_score < 20:
        missing = []
        if str(name).lower() == 'not detected':
            missing.append('full name')
        if str(email).lower() == 'not detected':
            missing.append('email address')
        if str(phone).lower() == 'not detected':
            missing.append('phone number')
        if missing:
            suggestions.append(f"Add missing contact info: {', '.join(missing)}")

    if skills_score < 20:
        suggestions.append('Add more technical skills to a dedicated Skills section (aim for 6+)')

    if education_score < 10:
        suggestions.append('Add an Education section with your degree and institution name')

    if experience_score < 10:
        suggestions.append('Add an Experience or Internship section with job titles and dates')

    if keywords_score < 15:
        suggestions.append('Include more action verbs: led, built, designed, improved, delivered')

    if length_score < 10:
        suggestions.append('Aim for 300-800 words for optimal ATS performance')

    # Base score before final check
    initial_score = total_score
    
    # FINAL CHECK: Ensure score doesn't reach 100 unless ALL conditions are met
    if initial_score >= 90:
        # Check all conditions for a "perfect" resume
        perfect_conditions = [
            has_name and not name_matches_email_prefix,  # Name detected and valid
            has_email,  # Email detected
            has_phone,  # Phone detected
            skill_count >= 8,  # Has 8+ skills
            has_degree and not is_in_progress,  # Has completed degree (not just in-progress)
            len(experience_list) >= 2,  # 2+ work entries
            action_verbs_count >= 5,  # 5+ action verbs
            400 <= word_count_value <= 700  # Word count in ideal range
        ]
        
        if not all(perfect_conditions):
            # Cap at 93 if not all conditions met
            total_score = min(93, initial_score)
    
    # Ensure score is within 0-100 range
    score = max(0, min(100, total_score))
    
    # Determine missing sections
    missing_sections = []
    if contact_score < 20:
        missing_sections.append("Complete Contact Information")
    if skills_score < 20:
        missing_sections.append("Skills Section")
    if education_score < 10:
        missing_sections.append("Education Section")
    if experience_score < 10:
        missing_sections.append("Experience Section")
    
    # Check for critical missing fields
    has_critical_issues = not has_name or not has_email or not has_phone
    
    # Add summary suggestion based on score and remaining issues
    if score >= 85 and not suggestions and not has_critical_issues:
        summary = "✅ Your resume is well-optimized for ATS systems!"
    elif score >= 60:
        summary = "🟡 Your resume is good, but can be improved. Follow the suggestions below."
    else:
        summary = "🔴 Your resume needs significant improvements for ATS optimization. Review the suggestions below."

    suggestions.insert(0, summary)
    
    return {
        'score': score,
        'breakdown': breakdown,
        'extracted_keywords': keywords,
        'missing_sections': missing_sections,
        'suggestions': suggestions,
        'word_count': word_count_value
    }

