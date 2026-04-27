"""
Scores resume formatting quality for ATS compatibility.
Works purely on extracted text.
"""
import re


def score_formatting(text: str) -> dict:
    """
    Returns:
    {
        "score": int (0-100),
        "issues": list[str],
        "passes": list[str],
    }
    """
    issues = []
    passes = []
    deductions = 0
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # 1. All-caps blocks (headers AND body text)
    # ── ALL CAPS section headers (1-4 words, no punctuation mid-line)
    all_caps_headers = [
        l for l in lines
        if l.isupper() and 1 <= len(l.split()) <= 4 and len(l) > 3
    ]
    all_caps_body = [
        l for l in lines
        if l.isupper() and len(l.split()) > 4
    ]

    if all_caps_headers:
        issues.append(
            f"Section headers are in ALL CAPS "
            f"({', '.join(all_caps_headers[:3])}). "
            f"Use Title Case instead — some ATS systems "
            f"misparse all-caps headers."
        )
        deductions += 8

    if all_caps_body:
        issues.append(
            "Large blocks of ALL CAPS text detected. "
            "Use normal sentence case throughout."
        )
        deductions += 10

    if not all_caps_headers and not all_caps_body:
        passes.append("No excessive all-caps text.")

    # 2. Bullet point usage
    bullet_pattern = re.compile(r'^[•\-\*▪○◦➢➤►]')
    bullet_lines = [l for l in lines if bullet_pattern.match(l)]
    total_lines = len(lines)

    if len(bullet_lines) < 5:
        issues.append(
            f"Only {len(bullet_lines)} bullet point(s) detected. "
            f"Use bullet points throughout to improve ATS parsing."
        )
        deductions += 15
    else:
        passes.append(
            f"Good use of bullet points "
            f"({len(bullet_lines)} detected)."
        )

    # 3. Sentence length in bullets
    long_bullets = [
        l for l in bullet_lines
        if len(l.split()) > 30
    ]
    if long_bullets:
        issues.append(
            f"{len(long_bullets)} bullet point(s) are too long "
            f"(>30 words). Keep bullets concise and scannable."
        )
        deductions += 10
    else:
        passes.append("Bullet point lengths look good.")

    # 4. Incomplete sentences detection
    # ── Lines that end mid-sentence ──────────────────────────────
    incomplete_lines = []
    INCOMPLETE_ENDINGS = {
        "and", "or", "but", "with", "to", "for",
        "in", "on", "at", "the", "a", "an",
        "where", "which", "that", "as",
    }
    for line in lines:
        words = line.split()
        # Line ends with a conjunction or preposition = incomplete
        if len(words) >= 3 and words[-1].lower() in INCOMPLETE_ENDINGS:
            incomplete_lines.append(line[:60])

    if incomplete_lines:
        issues.append(
            f"Incomplete sentence(s) detected — text appears to "
            f"cut off mid-sentence. Complete all sentences."
        )
        deductions += 15
    else:
        passes.append("No incomplete sentences detected.")

    # 5. Empty or near-empty sections
    # ── Detect section headers with no content ──────────────────
    SECTION_HEADER_RE = re.compile(
        r'^(experience|skills|education|projects|summary|'
        r'objective|certifications|achievements|work)',
        re.IGNORECASE
    )
    section_indices = [
        i for i, l in enumerate(lines)
        if SECTION_HEADER_RE.match(l.strip())
    ]
    empty_sections = []
    for idx in section_indices:
        # Check how many content lines follow before next section
        content_lines = 0
        for j in range(idx + 1, min(idx + 6, len(lines))):
            if SECTION_HEADER_RE.match(lines[j].strip()):
                break
            if len(lines[j].strip()) > 5:
                content_lines += 1
        if content_lines == 0:
            empty_sections.append(lines[idx].strip())

    if empty_sections:
        issues.append(
            f"Section(s) appear empty or have very little content: "
            f"{', '.join(empty_sections[:3])}. "
            f"Add meaningful content to each section."
        )
        deductions += 20
    else:
        passes.append("All sections have content.")

    # 6. Resume length check
    # ── Word count too short ────────────────────────────────────
    word_count = len(text.split())
    if word_count < 150:
        issues.append(
            f"Resume is very short ({word_count} words). "
            f"A strong resume typically has 300–800 words. "
            f"Expand your experience and skills sections."
        )
        deductions += 25
    elif word_count < 250:
        issues.append(
            f"Resume is short ({word_count} words). "
            f"Add more detail to your experience entries."
        )
        deductions += 12
    else:
        passes.append(f"Good resume length ({word_count} words).")

    # 7. Passive voice detection
    passive_patterns = re.compile(
        r'\b(was|were|been|being|is|are)\s+'
        r'(handled|managed|done|created|built|made|used|given|'
        r'assigned|developed|designed|tested|deployed)\b',
        re.IGNORECASE
    )
    passive_matches = passive_patterns.findall(text)
    if len(passive_matches) >= 3:
        issues.append(
            f"Detected {len(passive_matches)} passive voice "
            f"constructions. Use active voice: "
            f"'Built X' not 'X was built by me'."
        )
        deductions += 10
    else:
        passes.append("Mostly active voice - good.")

    # 8. Contact section presence
    has_email = bool(re.search(
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
        text
    ))
    has_phone = bool(re.search(
        r'(\+?\d[\d\s\-().]{7,}\d)', text
    ))
    if not has_email:
        issues.append("No email address detected.")
        deductions += 15
    else:
        passes.append("Email address present.")

    if not has_phone:
        issues.append("No phone number detected.")
        deductions += 10
    else:
        passes.append("Phone number present.")

    # 9. Appropriate line density
    very_short = [l for l in lines if len(l.split()) == 1]
    if total_lines > 0 and len(very_short) > total_lines * 0.4:
        issues.append(
            "Too many single-word lines detected - may indicate "
            "a multi-column layout that ATS cannot parse correctly."
        )
        deductions += 15
    else:
        passes.append("Line density looks ATS-friendly.")

    # 10. Section headers present
    header_terms = {
        "experience", "education", "skills",
        "projects", "certifications", "summary",
        "objective", "achievements",
    }
    text_lower = text.lower()
    found_headers = [h for h in header_terms if h in text_lower]

    if len(found_headers) < 3:
        issues.append(
            "Few standard section headers detected. "
            "Use clear labels: Experience, Education, Skills."
        )
        deductions += 15
    else:
        passes.append(
            f"Good section structure "
            f"({len(found_headers)} headers found)."
        )

    score = max(0, 100 - deductions)

    return {
        "score": score,
        "issues": issues,
        "passes": passes,
    }
