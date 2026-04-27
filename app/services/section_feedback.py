"""
Gives targeted feedback per resume section.
All logic is pattern-based - no hardcoded names.
"""
import re


def generate_section_feedback(
    text: str,
    ats_breakdown: dict,
    work_experience: list,
    education: list,
    extracted_skills: list,
) -> dict:
    """
    Returns per-section actionable feedback.

    Returns:
    {
        "contact":    {"status": str, "tips": list[str]},
        "experience": {"status": str, "tips": list[str]},
        "education":  {"status": str, "tips": list[str]},
        "skills":     {"status": str, "tips": list[str]},
        "summary":    {"status": str, "tips": list[str]},
        "overall":    list[str],
    }
    """

    feedback = {}
    text_lower = text.lower()

    # Contact section
    contact_tips = []
    has_email = bool(re.search(
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
        text
    ))
    has_phone = bool(re.search(
        r'(\+?\d[\d\s\-().]{7,}\d)', text
    ))
    has_linkedin = bool(re.search(
        r'linkedin\.com/in/', text, re.IGNORECASE
    ))
    has_github = bool(re.search(
        r'github\.com/', text, re.IGNORECASE
    ))

    if not has_email:
        contact_tips.append("Add a professional email address.")
    if not has_phone:
        contact_tips.append("Add a phone number.")
    if not has_linkedin:
        contact_tips.append(
            "Add your LinkedIn URL - many ATS systems "
            "require it for screening."
        )
    if not has_github:
        contact_tips.append(
            "Add your GitHub or portfolio URL - "
            "essential for technical roles."
        )

    contact_status = "Good" if not contact_tips else (
        "Needs Work" if len(contact_tips) >= 2 else "Fair"
    )
    feedback["contact"] = {
        "status": contact_status,
        "tips": contact_tips or [
            "Contact section looks complete."
        ],
    }

    # Experience section
    exp_tips = []
    action_verbs = {
        "managed", "built", "developed", "led", "designed",
        "implemented", "created", "improved", "optimized",
        "delivered", "launched", "engineered", "automated",
        "deployed", "increased", "reduced", "streamlined",
        "collaborated", "spearheaded", "coordinated",
        "researched", "analysed", "analyzed", "presented",
    }
    found_verbs = [v for v in action_verbs if v in text_lower]

    # Helper: Check if experience entries have real content
    def has_real_content(exp_list: list) -> bool:
        """Returns True only if entries have title AND
        at least some description or company info."""
        for exp in exp_list:
            title = (exp.get("title") or "").strip()
            desc = (exp.get("description") or "").strip()
            company = (exp.get("company") or "").strip()
            # Must have a title with more than 2 words
            # OR a description with more than 5 words
            # OR a company name
            if (len(title.split()) >= 2 or
                len(desc.split()) >= 5 or
                len(company.split()) >= 1):
                return True
        return False

    if not work_experience or not has_real_content(work_experience):
        exp_tips.append(
            "No meaningful work experience detected. "
            "Add internships, freelance projects, academic projects, "
            "or volunteer work with descriptions of what you did."
        )
        exp_tips.append(
            "Even personal/academic projects count — describe "
            "what you built, what technologies you used, "
            "and what impact it had."
        )
    else:
        if len(work_experience) == 1:
            exp_tips.append(
                "Only one experience entry detected. "
                "Include internships, freelance, or projects "
                "if you have limited full-time experience."
            )

        # Check for quantified achievements
        number_pattern = re.compile(r'\d+\s*[%xX]?|\$\s*\d+|\d+\+')
        has_numbers = bool(number_pattern.search(text))
        if not has_numbers:
            exp_tips.append(
                "No quantified achievements found. "
                "Add numbers to make impact clear: "
                "'Improved performance by 30%', "
                "'Built app used by 500+ students'."
            )

        if len(found_verbs) < 3:
            exp_tips.append(
                f"Only {len(found_verbs)} action verb(s) detected. "
                f"Start every bullet point with a strong verb: "
                f"Built, Developed, Led, Designed, Improved."
            )

    exp_status = "Good" if not exp_tips else (
        "Needs Work" if len(exp_tips) >= 2 else "Fair"
    )
    feedback["experience"] = {
        "status": exp_status,
        "tips": exp_tips or [
            "Experience section looks strong."
        ],
    }

    # Education section
    edu_tips = []
    if not education:
        edu_tips.append(
            "No education section detected. Add a clearly "
            "labelled 'Education' section with institution "
            "and graduation year."
        )
    else:
        for edu in education:
            if not edu.get("year"):
                edu_tips.append(
                    "Add graduation year(s) to your education "
                    "entries - ATS systems use them for filtering."
                )
                break
            if not edu.get("degree"):
                edu_tips.append(
                    "Add your degree/qualification name to "
                    "education entries."
                )
                break

    edu_status = "Good" if not edu_tips else "Fair"
    feedback["education"] = {
        "status": edu_status,
        "tips": edu_tips or [
            "Education section looks complete."
        ],
    }

    # Skills section
    skill_tips = []
    if not extracted_skills:
        skill_tips.append(
            "No recognised technical skills detected. "
            "Add a dedicated 'Skills' section listing specific "
            "technologies, languages, and tools."
        )
        skill_tips.append(
            "Generic skills like 'MS Office' or 'basics' don't "
            "score well. List specific tools: Python, SQL, React, etc."
        )
    elif len(extracted_skills) < 4:
        skill_tips.append(
            f"Only {len(extracted_skills)} technical skill(s) detected. "
            f"ATS systems expect at least 8-12 relevant skills. "
            f"Expand your skills section significantly."
        )
        skill_tips.append(
            "Avoid vague entries like 'basics' or 'fundamentals' — "
            "list the actual technology name."
        )
    elif len(extracted_skills) < 8:
        skill_tips.append(
            f"{len(extracted_skills)} skills detected — below average. "
            f"Add more specific technical skills, tools, and frameworks "
            f"relevant to your target role."
        )
    else:
        # Check skill diversity
        has_lang = any(
            s.lower() in {
                "python", "java", "javascript", "typescript",
                "c++", "go", "rust", "sql", "r"
            }
            for s in extracted_skills
        )
        has_cloud = any(
            s.lower() in {"aws", "gcp", "azure", "docker", "kubernetes"}
            for s in extracted_skills
        )
        if not has_cloud:
            skill_tips.append(
                "Consider adding cloud/DevOps skills "
                "(AWS, GCP, Docker) - highly valued in "
                "most technical roles."
            )

    skill_status = "Good" if len(extracted_skills) >= 8 else (
        "Fair" if len(extracted_skills) >= 4 else "Needs Work"
    )
    feedback["skills"] = {
        "status": skill_status,
        "tips": skill_tips or [
            f"Good skills coverage "
            f"({len(extracted_skills)} skills detected)."
        ],
    }

    # Summary/Objective section
    summary_tips = []
    has_summary = any(
        kw in text_lower
        for kw in ["summary", "objective", "profile", "about me"]
    )
    if not has_summary:
        summary_tips.append(
            "Add a 2-3 sentence professional summary at the top. "
            "It's the first thing recruiters read."
        )
    else:
        # Check for incomplete objective
        summary_match = re.search(
            r'(summary|objective|profile|about me)'
            r'(.{10,400})',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if summary_match:
            summary_text = summary_match.group(2).strip()
            word_count = len(summary_text.split())
            last_word = summary_text.split()[-1].lower() \
                        if summary_text.split() else ""

            INCOMPLETE_ENDINGS = {
                "and", "or", "but", "with", "to", "for",
                "in", "on", "at", "the", "a", "an",
                "where", "which", "that", "as", "enhance",
                "learn", "develop", "improve",
            }

            if last_word in INCOMPLETE_ENDINGS:
                summary_tips.append(
                    "Your objective/summary appears to be incomplete "
                    "— it ends mid-sentence. Complete the thought."
                )
            elif word_count < 15:
                summary_tips.append(
                    "Your summary is too brief. Write 2-3 complete "
                    "sentences about your goals and key strengths."
                )
            elif word_count > 80:
                summary_tips.append(
                    "Summary is too long. Keep it to 2-3 sentences."
                )

    summary_status = "Good" if not summary_tips else "Fair"
    feedback["summary"] = {
        "status": summary_status,
        "tips": summary_tips or [
            "Professional summary looks good."
        ],
    }

    # Overall quick wins
    overall = []
    weak_count = sum(
        1 for v in feedback.values()
        if isinstance(v, dict) and v.get("status") == "Needs Work"
    )
    fair_count = sum(
        1 for v in feedback.values()
        if isinstance(v, dict) and v.get("status") == "Fair"
    )

    if weak_count == 0 and fair_count == 0:
        overall.append(
            "All sections look strong. Focus on tailoring "
            "keywords for each specific job application."
        )
    else:
        overall.append(
            f"{weak_count + fair_count} section(s) need attention. "
            f"Address the highest priority items first."
        )

    feedback["overall"] = overall
    return feedback
