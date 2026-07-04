import json
import os
import re
from datetime import datetime
from typing import Any

from google import genai


def _truncate_text(text: str, limit: int = 8000) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    return text[:limit]


def _clean_json_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_json_payload(text: str) -> dict[str, Any]:
    cleaned = _clean_json_text(text)
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    raise ValueError("Gemini response did not contain valid JSON")


def analyse_job_description(job_description: str) -> dict[str, Any]:
    text = job_description or ""
    required = []
    preferred = []

    for line in re.split(r"\n|•|\*", text):
        item = line.strip()
        if not item:
            continue
        lowered = item.lower()
        if any(token in lowered for token in ("required", "must have", "must", "minimum", "need to")):
            required.append(item)
        elif any(token in lowered for token in ("preferred", "nice to have", "bonus", "plus")):
            preferred.append(item)

    years_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience", text, re.IGNORECASE)
    if years_match:
        years = int(years_match.group(1))
        if years >= 7:
            experience_level = "Senior"
        elif years >= 4:
            experience_level = "Mid-level"
        else:
            experience_level = "Junior"
    else:
        experience_level = "Unspecified"

    return {
        "required_skills": required[:6],
        "preferred_skills": preferred[:6],
        "experience_level": experience_level,
    }


def _fallback_review(job_match: dict[str, Any] | None) -> dict[str, Any]:
    job_match = job_match or {}
    match_score = int(job_match.get("match_score") or job_match.get("semantic_score") or 0)
    if match_score >= 70:
        experience_fit = "Good"
    elif match_score >= 40:
        experience_fit = "Partial"
    else:
        experience_fit = "Poor"

    matched = list(job_match.get("matched_keywords") or [])[:8]
    missing = list(job_match.get("missing_keywords") or [])[:8]

    return {
        "match_score": match_score,
        "experience_fit": experience_fit,
        "matched_skills": matched,
        "missing_skills": missing,
        "explanation": (
            "Gemini review was unavailable, so this summary falls back to the existing "
            "semantic and keyword match signals."
        ),
        "recommendations": [
            "Highlight the strongest overlapping skills near the top of the resume.",
            "Add measurable outcomes around the missing JD terms where they are genuinely accurate.",
        ],
        "source": "fallback",
    }


def generate_jd_review(
    resume_text: str,
    job_description: str,
    job_match: dict[str, Any] | None = None,
    extracted_skills: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a structured JD review using Gemini, with a deterministic fallback."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback_review(job_match)

    try:
        client = genai.Client(api_key=api_key)
        current_year = datetime.now().year
        jd_analysis = analyse_job_description(job_description)
        overlap = {
            "existing_match_score": (job_match or {}).get("match_score"),
            "matched_keywords": (job_match or {}).get("matched_keywords", [])[:12],
            "missing_keywords": (job_match or {}).get("missing_keywords", [])[:12],
            "resume_skills": (extracted_skills or [])[:20],
        }

        prompt = (
            "You are a senior technical recruiter reviewing a resume against a job description. "
            "Use the provided JD analysis and overlap hints, but judge the candidate from the actual resume text. "
            f"Current year: {current_year}. "
            "Return ONLY valid JSON with exactly these keys: match_score, experience_fit, matched_skills, "
            "missing_skills, explanation, recommendations. "
            "Rules: match_score must be an integer 0-100; experience_fit must be one of Good, Partial, Poor; "
            "matched_skills and missing_skills must be arrays of short phrases; explanation must be 2-4 concise sentences; "
            "recommendations must be an array of 3-5 actionable bullets. "
            "Do not mention that you are an AI. Do not wrap the JSON in markdown. "
            "Ensure matched_skills and missing_skills strictly contain professional or technical skills, avoiding locations, generic nouns, or soft filler words. "
            f"\n\nJD analysis:\n{json.dumps(jd_analysis, ensure_ascii=False)}"
            f"\n\nOverlap hints:\n{json.dumps(overlap, ensure_ascii=False)}"
            f"\n\nResume text:\n{_truncate_text(resume_text)}"
            f"\n\nJob description:\n{_truncate_text(job_description)}"
        )

        from app.utils.cache import get_cache_key, get_cached_json, set_cached_json
        cache_key = get_cache_key("jd_review_json", prompt)
        payload = get_cached_json(cache_key)
        
        if payload:
            print("[CACHE HIT] generate_jd_review")
        else:
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
                contents=prompt,
                config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                },
            )
            payload = _extract_json_payload(getattr(response, "text", "") or "")
            if payload:
                set_cached_json(cache_key, payload)

        return {
            "match_score": int(payload.get("match_score") or 0),
            "experience_fit": str(payload.get("experience_fit") or "Partial"),
            "matched_skills": list(payload.get("matched_skills") or [])[:10],
            "missing_skills": list(payload.get("missing_skills") or [])[:10],
            "explanation": str(payload.get("explanation") or ""),
            "recommendations": list(payload.get("recommendations") or [])[:5],
            "jd_analysis": jd_analysis,
            "source": "gemini",
        }
    except Exception as exc:
        print(f"[JD Review] Gemini review failed: {exc}")
        
        # Fallback to Hugging Face
        from app.services.hf_client import _hf_generate
        print("[JD Review] Attempting Hugging Face fallback...")
        hf_payload = _hf_generate(prompt, expect_json=True)
        if isinstance(hf_payload, dict):
            print("[JD Review] Fallback to HF succeeded.")
            return {
                "match_score": int(hf_payload.get("match_score") or 0),
                "experience_fit": str(hf_payload.get("experience_fit") or "Partial"),
                "matched_skills": list(hf_payload.get("matched_skills") or [])[:10],
                "missing_skills": list(hf_payload.get("missing_skills") or [])[:10],
                "explanation": str(hf_payload.get("explanation") or ""),
                "recommendations": list(hf_payload.get("recommendations") or [])[:5],
                "jd_analysis": jd_analysis,
                "source": "hf_fallback",
            }
            
        print("[JD Review] HF fallback failed, using basic fallback.")
        return _fallback_review(job_match)