import re


def extract_work_experience(text: str) -> list:
    """Extract work experience entries from resume text."""
    if not text:
        return []

    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    section_headers = [
        "work experience",
        "experience",
        "employment history",
        "work history",
        "internship",
        "internships",
        "professional experience",
    ]
    end_headers = [
        "projects",
        "education",
        "skills",
        "certifications",
        "achievements",
        "awards",
        "publications",
    ]

    start_idx = -1
    for header in section_headers:
        match = re.search(r"\b" + re.escape(header) + r"\b", normalized, re.IGNORECASE)
        if match and (start_idx == -1 or match.start() < start_idx):
            start_idx = match.end()

    if start_idx == -1:
        return []

    tail = normalized[start_idx:]
    end_idx = len(tail)
    for header in end_headers:
        match = re.search(r"\b" + re.escape(header) + r"\b", tail, re.IGNORECASE)
        if match and match.start() < end_idx:
            end_idx = match.start()

    section_text = tail[:end_idx].strip(" -|:")
    if not section_text:
        return []

    date_pattern = re.compile(
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}"
        r"(?:\s*(?:–|—|-|to)\s*|\s+)"
        r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}|present)\b"
        r"|\b\d{4}\s*(?:–|—|-|to|\s+)\s*(?:\d{4}|present)\b",
        re.IGNORECASE,
    )
    date_matches = list(date_pattern.finditer(section_text))

    experiences = []

    # Fallback: section exists but no parseable date range.
    if not date_matches:
        return [
            {
                "title": "Experience",
                "company": "",
                "duration": "",
                "description": section_text[:220],
            }
        ]

    for idx, date_match in enumerate(date_matches):
        prev_end = date_matches[idx - 1].end() if idx > 0 else 0
        next_start = date_matches[idx + 1].start() if idx + 1 < len(date_matches) else len(section_text)

        pre_block = section_text[prev_end:date_match.start()].strip(" -|:")
        post_block = section_text[date_match.end():next_start].strip(" -|:")
        duration = date_match.group(0).strip()

        title = ""
        company = ""

        if pre_block:
            # Common case in flattened text: company appears immediately before date.
            company_candidate = pre_block.strip(" ,-|:")
            company = company_candidate[:80]

        if post_block:
            # Infer role title from the beginning of text after date range.
            role_split = re.split(
                r"\b(remote|hybrid|onsite|present|spearheaded|managed|developed|designed|implemented|built|created|worked|led|analyzed)\b",
                post_block,
                maxsplit=1,
                flags=re.IGNORECASE,
            )
            role_candidate = role_split[0].strip(" ,-|:")
            if role_candidate:
                title = " ".join(role_candidate.split()[:8])

            # Keep remaining text as description.
            if title and post_block.lower().startswith(title.lower()):
                post_block = post_block[len(title):].strip(" ,-|:")

        if not title and company:
            # Fallback title when only company is detectable.
            title = "Experience"

        experiences.append(
            {
                "title": title,
                "company": company,
                "duration": duration,
                "description": post_block[:220],
            }
        )

    return experiences[:5]
