"""
Categorised keyword gap analysis between resume and job description.
Splits gaps into: technical skills, soft skills, tools, domain terms.
"""


# Generic category signal words - no role-specific hardcoding
SOFT_SKILL_SIGNALS = {
    "communication", "leadership", "teamwork", "collaboration",
    "problem solving", "critical thinking", "adaptability",
    "time management", "creativity", "attention to detail",
    "interpersonal", "presentation", "negotiation", "mentoring",
    "decision making", "analytical", "organised", "proactive",
    "self motivated", "multitasking", "conflict resolution",
}

TOOL_SIGNALS = {
    "jira", "confluence", "slack", "notion", "trello", "asana",
    "github", "gitlab", "bitbucket", "jenkins", "postman",
    "figma", "sketch", "adobe", "excel", "powerpoint", "word",
    "tableau", "powerbi", "looker", "metabase",
    "vs code", "intellij", "pycharm", "android studio",
}


def categorise_keyword_gaps(
    resume_text: str,
    job_description: str,
    current_missing: list,
) -> dict:
    """
    Takes the existing missing keywords list and categorises them.
    Also generates a before/after score simulation.

    Returns:
    {
        "technical": list[str],
        "soft_skills": list[str],
        "tools": list[str],
        "domain": list[str],
        "simulation": {
            "current_score": int,
            "potential_score": int,
            "keywords_to_add": list[str],
            "score_gain": int,
        }
    }
    """
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    technical = []
    soft_skills = []
    tools = []
    domain = []

    for kw in current_missing:
        kw_lower = kw.lower().strip()

        if kw_lower in SOFT_SKILL_SIGNALS or any(
            s in kw_lower for s in SOFT_SKILL_SIGNALS
        ):
            soft_skills.append(kw)
        elif kw_lower in TOOL_SIGNALS or any(
            t in kw_lower for t in TOOL_SIGNALS
        ):
            tools.append(kw)
        elif (
            # Heuristic: short words (1-2) that appear in JD
            # but not resume = likely technical terms
            len(kw_lower.split()) <= 2
            and kw_lower not in resume_lower
        ):
            technical.append(kw)
        else:
            domain.append(kw)

    # Score simulation
    # Estimate: each added keyword raises match score by ~3pts
    # capped at 95
    all_missing = technical + soft_skills + tools + domain
    keywords_to_add = all_missing[:5]
    score_gain = min(len(keywords_to_add) * 4, 30)

    # Try to read current match score from job_description context
    # (caller should pass it; here we estimate from gap size)
    gap_ratio = len(all_missing) / max(
        len(jd_lower.split()), 1
    )
    est_current = max(10, 100 - int(gap_ratio * 200))
    est_potential = min(95, est_current + score_gain)

    return {
        "technical": technical,
        "soft_skills": soft_skills,
        "tools": tools,
        "domain": domain,
        "simulation": {
            "current_score": est_current,
            "potential_score": est_potential,
            "keywords_to_add": keywords_to_add,
            "score_gain": score_gain,
        },
    }
