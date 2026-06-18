import json
import os
import re
import time
from difflib import SequenceMatcher
from typing import Dict, List, Any

from google import genai

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

MAX_RETRIES = 3
RETRY_DELAY = 2
USE_GEMINI_SEMANTIC_SIMILARITY = os.getenv("USE_GEMINI_SEMANTIC_SIMILARITY", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def _truncate_text(text: str, limit: int = 3500) -> str:
    return str(text or "").strip()[:limit]


def _clean_json_text(text: str) -> str:
    cleaned = str(text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_json_payload(text: str) -> dict:
    cleaned = _clean_json_text(text)
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    raise ValueError("Gemini response did not contain valid JSON")


def _gemini_generate_json(prompt: str) -> dict | None:
    client = _get_gemini_client()
    if client is None:
        return None

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )
    return _extract_json_payload(getattr(response, "text", "") or "")


def _local_similarity_fallback(text_a: str, text_b: str) -> float | None:
    words_a = {w for w in re.findall(r"[a-zA-Z0-9+#.]+", text_a.lower()) if len(w) > 2}
    words_b = {w for w in re.findall(r"[a-zA-Z0-9+#.]+", text_b.lower()) if len(w) > 2}
    if not words_a or not words_b:
        return None

    overlap = len(words_a & words_b)
    union = len(words_a | words_b)
    token_score = (overlap / union) if union else 0.0

    normalized_a = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+#.\s]", " ", text_a.lower())).strip()
    normalized_b = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+#.\s]", " ", text_b.lower())).strip()
    sequence_score = SequenceMatcher(None, normalized_a, normalized_b).ratio()

    blended = (token_score * 0.65) + (sequence_score * 0.35)
    return round(max(0.0, min(1.0, blended)), 4)


def extract_contact_info(resume_text: str) -> Dict[str, str]:
    """
    Extract contact information (name, email, phone) using pure regex and heuristics.
    This replaces NER-based contact extraction which is unreliable.
    
    Returns:
        dict: Contact info with keys 'name', 'email', 'phone' (values are strings or 'Not detected')
    """
    lines = [l.strip() for l in (resume_text or '').split('\n') if l.strip()]

    # --- EMAIL (regex, always reliable) ---
    email_pattern = r'[\w\.\+\-]+@[\w\.\-]+\.[a-zA-Z]{2,}'
    email = None
    for line in lines:
        match = re.search(email_pattern, line)
        if match:
            email = match.group(0).strip().lower()
            break

    # Fallback for wrapped/spaced variants like "name @ domain . com".
    if not email:
        full_text = '\n'.join(lines)
        spaced_email_pattern = r'[\w\.\+\-]+\s*@\s*[\w\.\-]+\s*\.\s*[a-zA-Z]{2,}'
        match = re.search(spaced_email_pattern, full_text)
        if match:
            email = re.sub(r'\s+', '', match.group(0)).lower()

    # --- PHONE (regex) ---
    # Handles common international and local phone formats with separators/parentheses.
    phone_pattern = r'((?:\+?\d{1,3}[\s\-.]?)?(?:\(\d{1,4}\)[\s\-.]?)?[\d\s\-.]{7,20}\d)'
    phone = None

    def _extract_phone_from_text(candidate_text: str) -> str:
        normalized = (
            candidate_text
            .replace('\u00a0', ' ')
            .replace('\u2013', '-')
            .replace('\u2014', '-')
        )
        for match in re.finditer(phone_pattern, normalized):
            candidate = re.sub(r'\s+', ' ', match.group(1)).strip(' .-')
            digits = re.sub(r'\D', '', candidate)
            if 7 <= len(digits) <= 15:
                return candidate
        return None

    for line in lines:
        lower_line = line.lower()
        if '@' in lower_line or 'http' in lower_line:
            continue
        phone = _extract_phone_from_text(line)
        if phone:
            break

    # Fallback: scan entire resume text in case line splitting breaks number groups.
    if not phone:
        full_text = '\n'.join(lines)
        phone = _extract_phone_from_text(full_text)

    # --- NAME ---
    email_blacklist = set()
    if email:
        prefix = email.split('@')[0].lower()
        email_blacklist.add(prefix)
        for i in range(len(prefix)):
            for j in range(i + 4, len(prefix) + 1):
                email_blacklist.add(prefix[i:j])

    skip_words = {
        'resume', 'cv', 'curriculum', 'vitae', 'summary', 'objective',
        'profile', 'contact', 'address', 'phone', 'email', 'linkedin',
        'github', 'portfolio', 'reference', 'skill', 'skills', 'education',
        'experience', 'project', 'projects', 'certification', 'certifications',
        'award', 'awards', 'language', 'languages', 'interests', 'about',
        'core', 'tools', 'frontend', 'backend', 'database', 'work',
        'intern', 'developer', 'engineer', 'analyst', 'designer', 'manager',
        'web', 'software', 'data', 'lead', 'senior', 'junior', 'associate',
        'trainee', 'assistant', 'coordinator', 'specialist',
        'remote', 'technology',
        'university', 'college', 'institute', 'school', 'high'
    }

    address_indicators = {
        'state', 'country', 'district', 'city', 'road', 'street', 'st', 'lane', 'ln',
        'avenue', 'ave', 'sector', 'block', 'pin', 'zipcode', 'postal', 'address'
    }

    name = None
    for line in lines[:20]:
        if any(c in line for c in ['@', '/', '\\', '|', '+', '#']):
            continue
        lower_line = line.lower()
        if 'http' in lower_line or 'www.' in lower_line:
            continue
        if ',' in line:
            continue

        clean = re.sub(r'[^\w\s]', ' ', line).strip()
        clean = re.sub(r'\s+', ' ', clean).strip()
        words = clean.split()

        if len(words) < 2 or len(words) > 4:
            continue
        if any(w[0].isdigit() for w in words if w):
            continue
        if any(w.lower() in address_indicators for w in words):
            continue
        if any(w.lower() in skip_words for w in words):
            continue

        def looks_like_name_word(w: str) -> bool:
            return (
                len(w) >= 2
                and w.isalpha()
                and (w[0].isupper() or w.isupper())
            )

        if all(looks_like_name_word(w) for w in words):
            name = ' '.join(w.capitalize() for w in words)
            break

    return {
        'name': name or 'Not detected',
        'email': email or 'Not detected',
        'phone': phone or 'Not detected'
    }


def extract_name_fallback(text: str) -> str:
    """
    Fallback: grab the first non-empty line of resume as candidate name.
    Validates it looks like a name (2-4 words, all capitalized, no numbers).
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:5]:  # check first 5 lines only
        words = line.split()
        if (2 <= len(words) <= 4
                and all(w[0].isupper() for w in words if w)
                and not any(char.isdigit() for char in line)
                and "@" not in line):
            return line
    return None


def extract_email_fallback(text: str) -> str:
    """Fallback: extract email using regex"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None


def extract_phone_fallback(text: str) -> str:
    """Fallback: extract phone number using regex"""
    phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}'
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else None


def extract_skills_fallback(text: str) -> list:
    """Fallback: extract skills by looking for common keywords"""
    skills_keywords = [
        'python', 'java', 'javascript', 'typescript', 'csharp', 'cpp', 'ruby', 'php', 'swift', 'kotlin',
        'react', 'vue', 'angular', 'django', 'flask', 'fastapi', 'spring', 'nodejs', 'express',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github',
        'html', 'css', 'sass', 'bootstrap', 'tailwind',
        'git', 'linux', 'unix', 'windows', 'macos',
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
        'data analysis', 'data science', 'analytics', 'tableau', 'power bi',
        'agile', 'scrum', 'jira', 'confluence',
        'rest api', 'graphql', 'microservices', 'soap',
        'testing', 'pytest', 'junit', 'selenium', 'cypress'
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in skills_keywords:
        if skill in text_lower and skill not in found_skills:
            found_skills.append(skill)
    
    return found_skills[:15]  # Return top 15


def get_semantic_similarity(text_a, text_b):
    """
    Compute semantic similarity between two text inputs.
    Returns a float between 0 and 1, or None on failure.
    """
    # Guard: ensure both texts are strings and non-empty
    text_a = str(text_a or '').strip()
    text_b = str(text_b or '').strip()
    
    if not text_a or not text_b:
        print("[SIM] Empty text, skipping")
        return None

    # Default to deterministic local similarity so resume analysis stays within
    # Gemini RPM limits. Opt in to Gemini only when explicitly enabled.
    if not USE_GEMINI_SEMANTIC_SIMILARITY:
        fallback = _local_similarity_fallback(text_a, text_b)
        print(f"[SIM] Using local similarity score: {fallback}")
        return fallback
    
    try:
        prompt = (
            "You compare two text snippets for semantic similarity. "
            "Return ONLY valid JSON with keys score and reason. "
            "score must be a number from 0 to 1 where 1 means nearly identical meaning. "
            "Use meaning, not exact word overlap. "
            f"Text A: {_truncate_text(text_a)}\n"
            f"Text B: {_truncate_text(text_b)}"
        )

        print(f"[SIM] Sending Gemini request, text_a length: {len(text_a)}, text_b length: {len(text_b)}")
        result = _gemini_generate_json(prompt)
        if isinstance(result, dict) and "score" in result:
            score = round(float(result["score"]), 4)
            print(f"[SIM] Parsed Gemini score: {score}")
            return score

        fallback = _local_similarity_fallback(text_a, text_b)
        print(f"[SIM] Gemini unavailable, fallback score: {fallback}")
        return fallback
    except Exception as e:
        print(f"[SIM] Error: {e}")
        fallback = _local_similarity_fallback(text_a, text_b)
        print(f"[SIM] Fallback score after error: {fallback}")
        return fallback


def get_section_similarities(resume_sections, jd_text):
    """
    Compare each resume section with the job description.
    Returns dict: section_name -> similarity score.
    """
    results = {}
    for section_name, section_text in (resume_sections or {}).items():
        if not section_text or not str(section_text).strip():
            continue
        score = get_semantic_similarity(str(section_text), jd_text)
        if score is not None:
            results[section_name] = score
    return results


def get_requirement_coverage(jd_requirements, resume_text):
    """
    Score JD requirement lines against resume text.
    Levels: strong (>=0.70), partial (0.40-0.69), missing (<0.40)
    """
    results = []
    for req in jd_requirements or []:
        req = str(req).strip()
        if len(req) < 20:
            continue

        score = get_semantic_similarity((resume_text or "")[:1024], req)
        if score is None:
            continue

        if score >= 0.70:
            level = "strong"
        elif score >= 0.40:
            level = "partial"
        else:
            level = "missing"

        results.append({
            "requirement": req,
            "score": score,
            "level": level
        })
    return results


def extract_education_fallback(text: str) -> list:
    """Extract education entries using strict section-based parsing."""
    lines = [l.strip() for l in (text or '').split('\n') if l.strip()]

    edu_start_headers = [
        'education', 'academic background', 'academic qualifications',
        'qualifications', 'scholastic details', 'educational background'
    ]

    stop_headers = [
        'experience', 'work experience', 'employment', 'internship',
        'projects', 'project', 'skills', 'core skills', 'technical skills',
        'certifications', 'certification', 'awards', 'achievements',
        'publications', 'interests', 'hobbies', 'languages', 'summary',
        'objective', 'profile', 'about', 'contact', 'references'
    ]

    degree_keywords = [
        'bachelor', 'b.tech', 'b tech', 'b.e', 'bsc', 'b.sc', 'be',
        'master', 'm.tech', 'm tech', 'm.e', 'msc', 'm.sc', 'mba',
        'phd', 'ph.d', 'doctorate', 'diploma',
        'higher secondary', 'secondary', 'hsc', 'ssc',
        'technology', 'engineering', 'science', 'commerce', 'arts',
        'computer science', 'information technology',
        '10th', '12th', 'matriculation'
    ]

    institution_keywords = [
        'university', 'college', 'institute', 'school', 'iit', 'nit',
        'academy', 'polytechnic', 'vidyalaya', 'mahavidyalaya'
    ]

    edu_start_idx = None
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if len(line.split()) <= 4:
            if any(line_lower == h or line_lower.startswith(h) for h in edu_start_headers):
                edu_start_idx = i
                break

    if edu_start_idx is None:
        results = []
        for line in lines:
            line_lower = line.lower()
            has_degree = any(kw in line_lower for kw in degree_keywords)
            has_inst = any(kw in line_lower for kw in institution_keywords)
            if (has_degree or has_inst) and len(line.split()) >= 2 and len(line.split()) <= 12:
                results.append(line.strip())
        dedup = []
        seen = set()
        for line in results:
            key = line.lower()
            if key not in seen:
                seen.add(key)
                dedup.append(line)
        return dedup[:5]

    education_lines = []
    capturing = False

    for i, line in enumerate(lines):
        if i == edu_start_idx:
            capturing = True
            continue

        if not capturing:
            continue

        line_lower = line.lower().strip()

        if len(line.split()) <= 4:
            if any(line_lower == h or line_lower.startswith(h) for h in stop_headers):
                break

        has_degree = any(kw in line_lower for kw in degree_keywords)
        has_inst = any(kw in line_lower for kw in institution_keywords)
        has_year = bool(re.search(r'\b(19|20)\d{2}\b', line))

        word_count = len(line.split())
        if word_count > 12:
            continue

        if not has_degree and not has_inst and not has_year:
            continue

        education_lines.append(line.strip())

    result = []
    seen = set()
    for line in education_lines:
        key = line.lower()
        if key not in seen:
            seen.add(key)
            result.append(line)

    return result[:8]


def extract_certificates_fallback(text: str) -> list:
    """Extract certificates using section-based parsing instead of hardcoded keywords."""
    lines = [l.strip() for l in (text or '').split('\n') if l.strip()]

    cert_start_headers = [
        'certifications', 'certification', 'certificates', 'certificate',
        'courses', 'licenses', 'courses & certifications', 'licenses & certifications'
    ]

    stop_headers = [
        'experience', 'work experience', 'employment', 'internship',
        'projects', 'project', 'skills', 'core skills', 'technical skills',
        'education', 'academic background', 'academic qualifications',
        'awards', 'achievements', 'publications', 'interests', 'hobbies', 
        'languages', 'summary', 'objective', 'profile', 'about', 'contact', 'references'
    ]

    cert_start_idx = None
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if len(line.split()) <= 4:
            clean_header = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', line_lower)
            if any(clean_header == h for h in cert_start_headers):
                cert_start_idx = i
                break

    if cert_start_idx is None:
        return []

    cert_lines = []
    capturing = False

    for i, line in enumerate(lines):
        if i == cert_start_idx:
            capturing = True
            continue

        if not capturing:
            continue

        line_lower = line.lower().strip()
        
        if len(line.split()) <= 4:
            clean_header = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', line_lower)
            if any(clean_header == h for h in stop_headers):
                break

        if len(line) < 5:
            continue

        cert_lines.append(line.strip())

    result = []
    seen = set()
    for line in cert_lines:
        key = line.lower()
        if key not in seen:
            seen.add(key)
            result.append(line)

    return result[:10]


def extract_entities_fallback(text: str) -> Dict[str, Any]:
    """
    Fallback extraction using regex and pattern matching.
    Used when Hugging Face API is unavailable or fails.
    """
    return {
        "name": extract_name_fallback(text),
        "email": extract_email_fallback(text),
        "phone": extract_phone_fallback(text),
        "skills": extract_skills_fallback(text),
        "education": extract_education_fallback(text),
        "experience": [],
        "certificates": extract_certificates_fallback(text)
    }


def extract_entities(resume_text: str) -> Dict[str, Any]:
    """
    Extract named entities from resume.
    Uses pure regex + heuristics for contact info (name, email, phone).
    Uses NER model ONLY for skills extraction.
    Falls back gracefully if API is unavailable.
    
    Args:
        resume_text: Raw resume text
    
    Returns:
        dict: Extracted entities (name, email, phone, skills, education, experience)
    """
    # Extract contact info using pure regex + heuristics (NOT NER - NER is unreliable for this)
    contact_info = extract_contact_info(resume_text)
    
    entities = {
        "name": contact_info['name'],
        "email": contact_info['email'],
        "phone": contact_info['phone'],
        "skills": [],
        "education": extract_education_fallback(resume_text),  # Use fallback for education
        "experience": [],
        "certificates": extract_certificates_fallback(resume_text),
        "projects": []
    }
    
    try:
        prompt = (
            "Extract resume information and return ONLY valid JSON with keys name, email, phone, skills, education, experience, certificates, projects. "
            "skills must be a list of short technical skills. "
            "education must be a list of objects with keys: institution, degree, location, year. Ensure separate schools are separate objects. "
            "experience must be a list of objects with keys: title, company, duration, description. The 'description' must be an array of string bullet points. "
            "CRITICAL: 'experience' is ONLY for employment/work history. DO NOT include personal or academic projects here. "
            "projects must be a separate list of objects with keys: title, description (array of string bullet points). "
            "certificates must be a list of strings representing the names of certifications obtained. "
            f"Resume text: {_truncate_text(resume_text, 6000)}"
        )

        result = _gemini_generate_json(prompt)
        if isinstance(result, dict):
            skills = result.get("skills") or []
            if isinstance(skills, list) and skills:
                entities["skills"] = [str(skill).strip() for skill in skills if str(skill).strip()][:15]
            else:
                entities["skills"] = extract_skills_fallback(resume_text)

            print(
                f"[DEBUG Gemini] Extracted contact via regex: Name={entities['name']}, "
                f"Email={entities['email']}, Phone={entities['phone']}"
            )
            print(f"[DEBUG Gemini] Extracted skills via Gemini: {len(entities['skills'])} skills found")

            if isinstance(result.get("name"), str) and result.get("name").strip():
                entities["name"] = result["name"].strip()
            if isinstance(result.get("email"), str) and result.get("email").strip():
                entities["email"] = result["email"].strip()
            if isinstance(result.get("phone"), str) and result.get("phone").strip():
                entities["phone"] = result["phone"].strip()
            if isinstance(result.get("education"), list) and result.get("education"):
                entities["education"] = result.get("education")
            if isinstance(result.get("experience"), list) and result.get("experience"):
                entities["experience"] = result.get("experience")
            if isinstance(result.get("projects"), list) and result.get("projects"):
                entities["projects"] = result.get("projects")
            if isinstance(result.get("certificates"), list) and result.get("certificates"):
                gemini_certs = [str(c).strip() for c in result["certificates"] if str(c).strip()]
                combined_certs = entities["certificates"] + gemini_certs
                deduped_certs = []
                for c in combined_certs:
                    c_clean = re.sub(r'[^a-z0-9]+', ' ', c.lower()).strip()
                    if len(c_clean) < 3:
                        continue
                    is_duplicate = False
                    for i, existing in enumerate(deduped_certs):
                        existing_clean = re.sub(r'[^a-z0-9]+', ' ', existing.lower()).strip()
                        if c_clean in existing_clean:
                            is_duplicate = True
                            break
                        elif existing_clean in c_clean:
                            is_duplicate = True
                            deduped_certs[i] = c
                            break
                    if not is_duplicate:
                        deduped_certs.append(c)
                entities["certificates"] = deduped_certs

            return entities

        entities['skills'] = extract_skills_fallback(resume_text)
        print(f"[DEBUG Gemini] Gemini unavailable, using fallback skills: {len(entities['skills'])} skills found")
        return entities
    
    except Exception as api_error:
        print(f"[DEBUG Gemini] API error during skills extraction, using fallback: {str(api_error)}")
        entities['skills'] = extract_skills_fallback(resume_text)
        print(f"[DEBUG Gemini] Extracted contact via regex: Name={entities['name']}, Email={entities['email']}, Phone={entities['phone']}")
        print(f"[DEBUG Gemini] Extracted skills via fallback: {len(entities['skills'])} skills found")
        return entities


def call_ner_model(resume_text: str) -> Dict[str, Any]:
    """
    Backward-compatible NER API used by older route handlers.

    Current extraction returns `skills`; legacy callers expect `keywords`.
    """
    entities = extract_entities(resume_text)
    return {
        "name": entities.get("name"),
        "email": entities.get("email"),
        "phone": entities.get("phone"),
        "keywords": entities.get("skills", []),
        "skills": entities.get("skills", []),
        "education": entities.get("education", []),
        "experience": entities.get("experience", []),
        "certificates": entities.get("certificates", []),
        "projects": entities.get("projects", []),
    }


def get_job_match(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Calculate semantic similarity between resume and job description.
    Falls back to keyword matching if API is unavailable.
    
    Args:
        resume_text: Resume text
        job_description: Job description text
    
    Returns:
        dict: Similarity score (0-100) and matched keywords
    """
    try:
        prompt = (
            "Compare the resume and job description for fit. Return ONLY valid JSON with keys match_score, "
            "matched_keywords, missing_keywords. match_score must be an integer 0-100. "
            "matched_keywords and missing_keywords must be short phrase arrays. "
            f"Resume: {_truncate_text(resume_text, 5000)}\n"
            f"Job description: {_truncate_text(job_description, 5000)}"
        )

        result = _gemini_generate_json(prompt)
        if isinstance(result, dict):
            matched_keywords = result.get("matched_keywords") or []
            missing_keywords = result.get("missing_keywords") or []
            return {
                "match_score": max(0, min(100, int(result.get("match_score") or 0))),
                "matched_keywords": [str(item).strip() for item in matched_keywords if str(item).strip()][:20],
                "missing_keywords": [str(item).strip() for item in missing_keywords if str(item).strip()][:20],
            }

        resume_words = set(resume_text.lower().split())
        job_words = set(job_description.lower().split())
        matched_keywords = list(resume_words & job_words)
        missing_keywords = list(job_words - resume_words)
        return {
            "match_score": max(0, min(100, int((len(matched_keywords) / len(job_words)) * 100))) if job_words else 0,
            "matched_keywords": matched_keywords[:20],
            "missing_keywords": missing_keywords[:20]
        }
    
    except Exception as api_error:
        # Fallback: Simple keyword matching without Gemini
        resume_words = set(word.lower() for word in resume_text.split() if len(word) > 3)
        job_words = set(word.lower() for word in job_description.split() if len(word) > 3)
        
        matched_keywords = list(resume_words & job_words)
        missing_keywords = list(job_words - resume_words)
        
        # Calculate simple match score based on keyword overlap
        if job_words:
            match_score = int((len(matched_keywords) / len(job_words)) * 100)
        else:
            match_score = 0
        
        return {
            "match_score": max(0, min(100, match_score)),
            "matched_keywords": matched_keywords[:20],
            "missing_keywords": missing_keywords[:20]
        }
