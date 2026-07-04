import os
import json
import re
from google import genai
from typing import List

def _clean_json_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()

def rewrite_bullet(bullet_text: str) -> List[str]:
    """
    Takes a single work experience or project bullet point and returns 3 high-impact
    STAR method variations using Gemini.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Fallback if no API key is available
        return [
            f"Improved: {bullet_text}",
            f"Optimized: {bullet_text}",
            f"Successfully executed: {bullet_text}"
        ]

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = (
            "You are an expert resume writer. The user provided a text from their resume (either a professional summary or a bullet point). "
            "Rewrite it into 3 distinct, high-impact variations. If it is a bullet point, use the STAR method (Situation, Task, Action, Result) "
            "and focus on strong action verbs and quantitative metrics. If it is a summary, make it engaging and professional. "
            "Return ONLY a JSON array of exactly 3 strings. Do not include markdown formatting or explanations.\n\n"
            f"Original Text: {bullet_text}"
        )

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            contents=prompt,
            config={
                "temperature": 0.4,
                "response_mime_type": "application/json",
            },
        )
        
        response_text = getattr(response, "text", "") or ""
        cleaned = _clean_json_text(response_text)
        
        try:
            variations = json.loads(cleaned)
            if isinstance(variations, list) and len(variations) > 0:
                return [str(v) for v in variations[:3]]
        except Exception:
            pass

        return [f"Enhanced: {bullet_text}"]
    except Exception as exc:
        print(f"[Bullet Rewriter] Gemini failed: {exc}")
        
        from app.services.hf_client import _hf_generate
        print("[Bullet Rewriter] Attempting Hugging Face fallback...")
        hf_payload = _hf_generate(prompt, expect_json=True)
        
        if isinstance(hf_payload, list) and len(hf_payload) > 0:
            print("[Bullet Rewriter] Fallback to HF succeeded.")
            return [str(v) for v in hf_payload[:3]]
            
        return [f"Error rewriting: {bullet_text}"]
