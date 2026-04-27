import requests
import os
import time
import re
from typing import Dict, List, Any

HF_API_KEY = os.getenv('HF_API_KEY')
HF_API_URL = "https://api-inference.huggingface.co/models"

NER_MODEL = "yashpwr/resume-ner-bert-v2"
SIMILARITY_MODEL = "anass1209/resume-job-matcher-all-MiniLM-L6-v2"

MAX_RETRIES = 3
RETRY_DELAY = 2


def hf_post_with_retry(api_url, payload, headers, max_wait=60):
    """
    POST to HF API with retry logic for model cold start (503 loading).
    Retries up to max_wait seconds total.
    
    Args:
        api_url: Full HF API URL
        payload: Request payload dict
        headers: HTTP headers dict
        max_wait: Maximum total seconds to retry
    
    Returns:
        requests.Response object or None if all retries failed
    """
    start = time.time()
    attempt = 0

    while time.time() - start < max_wait:
        attempt += 1
        try:
            resp = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if resp.status_code == 200:
                return resp

            if resp.status_code == 503:
                body = {}
                try:
                    body = resp.json()
                except Exception:
                    pass

                estimated_wait = body.get('estimated_time', 10)
                estimated_wait = min(float(estimated_wait), 20)

                elapsed = time.time() - start
                print(f"[HF] Model loading (503), waiting {estimated_wait:.0f}s "
                      f"(attempt {attempt}, elapsed {elapsed:.0f}s)")
                time.sleep(estimated_wait)
                continue

            # Other error — return immediately
            print(f"[HF] Non-retryable error: {resp.status_code} {resp.text[:200]}")
            return resp

        except requests.exceptions.Timeout:
            print(f"[HF] Timeout on attempt {attempt}")
            time.sleep(5)
            continue
        except Exception as e:
            print(f"[HF] Request exception: {e}")
            return None

    elapsed = time.time() - start
    print(f"[HF] Gave up after {elapsed:.0f}s")
    return None


def get_headers():
    """Get headers for HF API requests."""
    return {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }


def call_hf_api(model: str, payload: Dict[str, Any], max_retries: int = MAX_RETRIES) -> Dict:
    """
    Make a request to Hugging Face Inference API with retry logic.
    
    Args:
        model: Model identifier
        payload: Request payload
        max_retries: Maximum number of retry attempts
    
    Returns:
        dict: API response
    
    Raises:
        Exception: If API call fails after retries
    """
    url = f"{HF_API_URL}/{model}"
    headers = get_headers()
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Handle model loading (503 error)
            if response.status_code == 503:
                if attempt < max_retries - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                raise Exception("Model is loading. Please try again in a moment.")
            
            # Handle rate limiting
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    time.sleep(RETRY_DELAY * (attempt + 2))
                    continue
                raise Exception("Rate limited. Please try again later.")
            
            # Handle other errors
            if response.status_code >= 400:
                raise Exception(f"API Error {response.status_code}: {response.text}")
            
            return response.json()
        
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
                continue
            raise Exception("API request timeout. Please try again.")
        
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
                continue
            raise Exception(f"API request failed: {str(e)}")
    
    raise Exception("API call failed after maximum retries")


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
    api_url = "https://api-inference.huggingface.co/models/anass1209/resume-job-matcher-all-MiniLM-L6-v2"
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}

    try:
        response = hf_post_with_retry(
            api_url,
            {
                "inputs": {
                    "source_sentence": (text_a or "")[:1024],
                    "sentences": [(text_b or "")[:1024]]
                }
            },
            headers,
            max_wait=60
        )
        
        if response is None or response.status_code != 200:
            print(f"[Semantic] API error: {response.status_code if response else 'No response'}")
            return None

        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            value = result[0]
            if isinstance(value, list) and len(value) > 0:
                value = value[0]
            return round(float(value), 4)

        if isinstance(result, dict):
            for key in ["similarity", "score", "cosine_similarity"]:
                if key in result:
                    return round(float(result[key]), 4)

        return None
    except Exception as e:
        print(f"[Semantic] Error: {e}")
        return None


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
        "experience": []
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
        "experience": []
    }
    
    # Use NER ONLY for skills extraction
    try:
        payload = {
            "inputs": resume_text
        }
        
        response = call_hf_api(NER_MODEL, payload)
        
        print(f"[DEBUG NER] Using NER model for skills extraction. Response type: {type(response)}")
        
        # Parse NER response - extract skills ONLY
        if isinstance(response, list) and len(response) > 0:
            if isinstance(response[0], list):
                for token_group in response[0]:
                    entity_group = token_group.get('entity_group', '').upper() if token_group.get('entity_group') else ''
                    score = token_group.get('score', 0)
                    word = token_group.get('word', '').strip()
                    
                    if score < 0.5:  # Skip low confidence predictions
                        continue
                    
                    # Extract SKILLS only from NER
                    if ('SKILLS' in entity_group or 'SKILL' in entity_group) and word:
                        if word not in entities['skills']:
                            entities['skills'].append(word)
        
        # Fallback: if NER didn't find skills, use keyword matching
        if not entities['skills']:
            entities['skills'] = extract_skills_fallback(resume_text)
        
        print(f"[DEBUG NER] Extracted contact via regex: Name={entities['name']}, Email={entities['email']}, Phone={entities['phone']}")
        print(f"[DEBUG NER] Extracted skills via NER: {len(entities['skills'])} skills found")
        return entities
    
    except Exception as api_error:
        # API failed, use fallback for skills
        print(f"[DEBUG NER] API error during skills extraction, using fallback: {str(api_error)}")
        entities['skills'] = extract_skills_fallback(resume_text)
        print(f"[DEBUG NER] Extracted contact via regex: Name={entities['name']}, Email={entities['email']}, Phone={entities['phone']}")
        print(f"[DEBUG NER] Extracted skills via fallback: {len(entities['skills'])} skills found")
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
        payload = {
            "inputs": {
                "source_sentence": resume_text,
                "sentences": [job_description]
            }
        }
        
        response = call_hf_api(SIMILARITY_MODEL, payload)
        
        # Parse similarity response
        match_score = 0
        
        if isinstance(response, list) and len(response) > 0:
            # Similarity score is typically between 0-1, scale to 0-100
            match_score = int(response[0] * 100) if isinstance(response[0], (int, float)) else 0
        
        # Extract keywords from both texts for comparison
        resume_words = set(resume_text.lower().split())
        job_words = set(job_description.lower().split())
        
        matched_keywords = list(resume_words & job_words)
        missing_keywords = list(job_words - resume_words)
        
        return {
            "match_score": max(0, min(100, match_score)),
            "matched_keywords": matched_keywords[:20],
            "missing_keywords": missing_keywords[:20]
        }
    
    except Exception as api_error:
        # Fallback: Simple keyword matching without API
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
