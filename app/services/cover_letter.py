import os
import json
from google import genai
from typing import Dict, Any

def generate_cover_letter(resume_data: Dict[str, Any], job_description: str) -> str:
    """
    Generates a personalized cover letter using Gemini based on resume data and the Job Description.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file."
        
    if not job_description or not job_description.strip():
        return "Error: No job description provided."
        
    try:
        client = genai.Client(api_key=api_key)
        
        name = resume_data.get("name", "[Your Name]")
        skills = resume_data.get("skills", [])
        experience = resume_data.get("experience", [])
        projects = resume_data.get("projects", [])
        education = resume_data.get("education", [])
        
        prompt = f"""
You are an expert career coach writing a highly personalized, professional cover letter.
Using the candidate's resume data and the provided Job Description, draft a tailored cover letter.
Adopt a confident, enthusiastic, and professional tone.

MANDATORY RULES:
1. Weave the candidate's most relevant skills into the letter to show why they are a great fit for the role.
2. Mention the candidate's education IF they appear to have less than 2 years of professional experience.
3. Explicitly mention 1-2 relevant projects by name.
4. Mention the specific skills or technologies used in those projects.
5. The cover letter MUST be strictly between 250 and 400 words.
6. Avoid generic, cliché phrases (e.g., "I am writing to apply for", "I am a highly motivated individual"). Hook the reader immediately.
7. If the company name or hiring manager is obvious from the Job Description, use it. Otherwise, use a standard professional greeting.
8. Do NOT wrap the output in markdown code blocks. Output ONLY the raw text of the cover letter, ready to be copied and pasted.

Candidate Name: {name}
Candidate Skills: {', '.join(skills) if isinstance(skills, list) else skills}
Candidate Experience (JSON): {json.dumps(experience)[:2500]}
Candidate Projects (JSON): {json.dumps(projects)[:1500]}
Candidate Education (JSON): {json.dumps(education)[:1000]}

Job Description:
{job_description[:5000]}
"""
        
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            contents=prompt,
            config={
                "temperature": 0.7, 
            },
        )
        
        text = response.text.strip()
        # Clean up any markdown code block artifacts
        if text.startswith("```"):
            lines = text.split("\n")
            if len(lines) > 1:
                text = "\n".join(lines[1:])
            if text.endswith("```"):
                text = text[:-3].strip()
                
        return text
    except Exception as exc:
        print(f"[Cover Letter Error] {exc}")
        return "An error occurred while generating the cover letter with AI. Please try again later."
