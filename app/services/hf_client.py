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


def extract_entities(resume_text: str) -> Dict[str, Any]:
    """
    Extract named entities from resume using NER model.
    
    Args:
        resume_text: Raw resume text
    
    Returns:
        dict: Extracted entities (name, email, phone, skills, education, experience)
    
    Raises:
        Exception: If API call fails
    """
    payload = {
        "inputs": resume_text
    }
    
    response = call_hf_api(NER_MODEL, payload)
    
    # Parse NER response
    entities = {
        "name": None,
        "email": None,
        "phone": None,
        "skills": [],
        "education": [],
        "experience": []
    }
    
    # Handle token classification response
    if isinstance(response, list) and len(response) > 0:
        if isinstance(response[0], list):
            # Token classification format
            for token_group in response[0]:
                entity_group = token_group.get('entity_group', '').upper()
                score = token_group.get('score', 0)
                word = token_group.get('word', '').strip()
                
                if score < 0.5:  # Skip low confidence predictions
                    continue
                
                if entity_group == 'NAME' and not entities['name']:
                    entities['name'] = word
                elif entity_group == 'EMAIL' and not entities['email']:
                    entities['email'] = word
                elif entity_group == 'PHONE' and not entities['phone']:
                    entities['phone'] = word
                elif entity_group == 'SKILLS' and word:
                    if word not in entities['skills']:
                        entities['skills'].append(word)
                elif entity_group == 'EDUCATION' and word:
                    if word not in entities['education']:
                        entities['education'].append(word)
                elif entity_group == 'EXPERIENCE' and word:
                    if word not in entities['experience']:
                        entities['experience'].append(word)
    
    # Fallback: Extract name if NER didn't find it
    if not entities['name']:
        entities['name'] = extract_name_fallback(resume_text)
    
    return entities


def get_job_match(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Calculate semantic similarity between resume and job description.
    
    Args:
        resume_text: Resume text
        job_description: Job description text
    
    Returns:
        dict: Similarity score (0-100) and matched keywords
    
    Raises:
        Exception: If API call fails
    """
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
