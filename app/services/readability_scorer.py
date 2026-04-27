"""
Scores how easy a resume is to scan in 6 seconds.
Based on sentence length, active voice, and structure.
"""
import re


def score_readability(text: str) -> dict:
    """
    Returns:
    {
        "score": int (0-100),
        "grade": str,
        "avg_sentence_length": int,
        "active_voice_pct": int,
        "feedback": list[str],
    }
    """
    feedback = []
    deductions = 0

    # Clean and tokenize
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.split()) > 3]
    words = text.split()

    if not sentences:
        return {
            "score": 50,
            "grade": "Unknown",
            "avg_sentence_length": 0,
            "active_voice_pct": 0,
            "feedback": ["Could not analyse readability."],
        }

    # 1. Average sentence length
    avg_len = sum(len(s.split()) for s in sentences) // len(sentences)

    if avg_len > 25:
        feedback.append(
            f"Average sentence length is {avg_len} words - "
            f"aim for under 20 words per sentence."
        )
        deductions += 20
    elif avg_len > 18:
        feedback.append(
            f"Sentences average {avg_len} words - "
            f"slightly long. Try to be more concise."
        )
        deductions += 10
    else:
        feedback.append(
            f"Good sentence length (avg {avg_len} words)."
        )

    # 2. Action verb usage
    action_verbs = {
        "managed", "developed", "built", "designed",
        "implemented", "led", "created", "improved",
        "optimized", "delivered", "achieved", "launched",
        "engineered", "automated", "deployed", "integrated",
        "collaborated", "coordinated", "spearheaded",
        "streamlined", "increased", "reduced", "drove",
        "established", "mentored", "negotiated",
    }
    text_lower = text.lower()
    found_verbs = [v for v in action_verbs if v in text_lower]

    if len(found_verbs) < 4:
        feedback.append(
            f"Only {len(found_verbs)} action verbs detected. "
            f"Start bullets with strong verbs: "
            f"Built, Led, Designed, Optimized."
        )
        deductions += 20
    elif len(found_verbs) < 8:
        feedback.append(
            f"{len(found_verbs)} action verbs found - "
            f"good, but more variety would strengthen impact."
        )
        deductions += 10
    else:
        feedback.append(
            f"Strong action verb usage "
            f"({len(found_verbs)} unique verbs)."
        )

    # 3. Passive voice
    passive_re = re.compile(
        r'\b(was|were|been|is|are)\s+'
        r'\w+ed\b',
        re.IGNORECASE
    )
    passive_count = len(passive_re.findall(text))
    total_sents = len(sentences)
    passive_pct = int((passive_count / max(total_sents, 1)) * 100)
    active_pct = max(0, 100 - passive_pct)

    if passive_pct > 30:
        feedback.append(
            f"High passive voice usage ({passive_pct}% of sentences). "
            f"Use active voice for stronger impact."
        )
        deductions += 15
    else:
        feedback.append(
            f"Good active voice ratio ({active_pct}% active)."
        )

    # 4. Filler word detection
    fillers = {
        "responsible for", "duties included",
        "helped with", "worked on", "assisted in",
        "involved in", "participated in",
    }
    fillers_found = [f for f in fillers if f in text_lower]
    if fillers_found:
        feedback.append(
            f"Weak phrases detected: "
            f"{', '.join(fillers_found[:3])}. "
            f"Replace with direct action verbs."
        )
        deductions += 15
    else:
        feedback.append("No weak filler phrases detected.")

    # 5. Word count appropriateness
    wc = len(words)
    if wc < 200:
        feedback.append(
            f"Resume is very short ({wc} words). "
            f"Add more detail to experience and skills."
        )
        deductions += 15
    elif wc > 1000:
        feedback.append(
            f"Resume is long ({wc} words). "
            f"Consider trimming to under 800 words."
        )
        deductions += 10
    else:
        feedback.append(f"Good word count ({wc} words).")

    score = max(0, 100 - deductions)

    if score >= 80:
        grade = "Excellent"
    elif score >= 60:
        grade = "Good"
    elif score >= 40:
        grade = "Fair"
    else:
        grade = "Needs Work"

    return {
        "score": score,
        "grade": grade,
        "avg_sentence_length": avg_len,
        "active_voice_pct": active_pct,
        "feedback": feedback,
    }
