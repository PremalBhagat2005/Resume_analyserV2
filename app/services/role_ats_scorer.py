"""
Role-specific ATS scoring when a job description is provided.
Re-weights the standard ATS score based on JD keyword density.
No hardcoded role names - all dynamic from JD content.
"""
import re
from collections import Counter


def score_role_specific_ats(
    resume_text: str,
    job_description: str,
    base_ats_score: int,
) -> dict:
    """
    Adjusts ATS score based on alignment with job description.

    Returns:
    {
        "adjusted_score": int,
        "base_score": int,
        "adjustment": int,
        "jd_keywords": list[str],
        "matched_jd_kw": list[str],
        "coverage_pct": int,
        "recommendation": str,
    }
    """
    # Extract meaningful words from JD
    # Strip stop words dynamically by frequency
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "as", "is", "are", "was",
        "were", "be", "been", "being", "have", "has", "had", "do",
        "does", "did", "will", "would", "could", "should", "may",
        "might", "shall", "can", "need", "must", "our", "we", "you",
        "your", "this", "that", "these", "those", "it", "its",
        "they", "them", "their", "who", "which", "what", "how",
        "when", "where", "why", "not", "no", "yes", "all", "any",
        "both", "each", "few", "more", "most", "other", "some",
        "such", "than", "then", "there", "too", "very", "just",
        "about", "above", "after", "before", "between", "into",
        "through", "during", "including", "across", "within",
    }

    # Extract words 3+ chars, not stop words
    jd_words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.]*\b',
                          job_description.lower())
    jd_words = [
        w for w in jd_words
        if len(w) >= 3 and w not in stop_words
    ]

    # Get top keywords by frequency (meaningful terms repeat)
    word_freq = Counter(jd_words)
    jd_keywords = [
        word for word, count in word_freq.most_common(30)
        if count >= 1
    ]

    # Match against resume
    resume_lower = resume_text.lower()
    matched = [
        kw for kw in jd_keywords
        if kw in resume_lower
    ]
    coverage_pct = int(
        len(matched) / max(len(jd_keywords), 1) * 100
    )

    # Calculate adjustment
    # Coverage >= 70% -> boost +5 to +10
    # Coverage 40-70% -> no change
    # Coverage < 40%  -> penalise -5 to -15
    if coverage_pct >= 70:
        adjustment = min(10, int((coverage_pct - 70) / 3))
    elif coverage_pct >= 40:
        adjustment = 0
    else:
        adjustment = -1 * min(15, int((40 - coverage_pct) / 3))

    adjusted_score = max(0, min(100, base_ats_score + adjustment))

    # Recommendation
    if coverage_pct >= 70:
        recommendation = (
            f"Strong keyword alignment with this role "
            f"({coverage_pct}% coverage). "
            f"Your resume is well-targeted."
        )
    elif coverage_pct >= 40:
        recommendation = (
            f"Moderate keyword coverage ({coverage_pct}%). "
            f"Add more role-specific terms from the job "
            f"description to improve your chances."
        )
    else:
        recommendation = (
            f"Low keyword coverage ({coverage_pct}%). "
            f"Your resume needs significant tailoring for "
            f"this specific role."
        )

    return {
        "adjusted_score": adjusted_score,
        "base_score": base_ats_score,
        "adjustment": adjustment,
        "jd_keywords": jd_keywords[:20],
        "matched_jd_kw": matched,
        "coverage_pct": coverage_pct,
        "recommendation": recommendation,
    }
