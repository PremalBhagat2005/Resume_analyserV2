import re


def extract_experience_fallback(resume_text: str) -> list:
    """
    Fallback extraction: look for experience section and extract lines as simple strings.
    This is used when the primary extractor returns nothing.
    """
    lines = resume_text.split('\n')
    
    experience_headers = [
        'work experience', 'experience', 'employment', 'employment history',
        'internship', 'internships', 'work history', 'professional experience',
        'positions', 'roles'
    ]
    
    date_pattern = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)[\w\s,.\-–—]{0,30}\d{4}'
    
    results = []
    capture = False
    capture_count = 0
    
    for i, line in enumerate(lines):
        line_lower = line.strip().lower()
        
        # Start capturing after experience header
        if any(header in line_lower for header in experience_headers):
            capture = True
            capture_count = 0
            continue
        
        # Stop capturing if we hit another major section
        stop_headers = ['education', 'skills', 'projects', 'certifications', 'awards', 'publications', 'references']
        if capture and any(h in line_lower for h in stop_headers) and len(line.strip()) < 40:
            capture = False
        
        if capture and line.strip():
            results.append(line.strip())
            capture_count += 1
            if capture_count >= 10:
                capture = False
    
    # Also scan entire text for lines with date ranges (e.g. "Nov 2025 – Jan 2026")
    if not results:
        for line in lines:
            if re.search(date_pattern, line.strip(), re.IGNORECASE) and len(line.strip()) > 10:
                results.append(line.strip())
    
    return results if results else []


def extract_work_experience(text: str) -> list:
    """
    Dynamically extract work experience from any resume.
    Uses only structural patterns — no hardcoded company or job title names.
    
    Pattern detection:
    - Finds experience section by generic keywords (experience, employment, etc.)
    - Uses date ranges to anchor each entry
    - Extracts company/employer and role from surrounding text
    - Works on ANY resume regardless of industry or employer
    """
    if not text:
        return []

    lines = text.split("\n")
    stripped_lines = [l.strip() for l in lines]

    # Generic section keywords — never hardcode specific companies/jobs
    EXP_START_TERMS = {
        "experience", "employment", "work history",
        "professional experience", "internship", "internships",
    }
    EXP_END_TERMS = {
        "education", "skills", "projects", "certifications",
        "certificate", "achievements", "publications", "awards",
        "training", "volunteer", "interests", "references",
    }

    # ── Step 1: Find experience section boundaries ──
    start_idx = None
    end_idx = len(stripped_lines)

    for i, line in enumerate(stripped_lines):
        line_lower = line.lower()
        word_count = len(line.split())

        # Section start: short line containing generic exp term
        if start_idx is None and word_count <= 5:
            if any(term in line_lower for term in EXP_START_TERMS):
                start_idx = i + 1

        # Section end: short line containing end term
        elif start_idx is not None and word_count <= 5:
            if any(term in line_lower for term in EXP_END_TERMS):
                end_idx = i
                break

    if start_idx is None:
        return []

    exp_lines = [l for l in stripped_lines[start_idx:end_idx] if l]

    # ── Step 2: Date regex — matches all common date formats ──
    DATE_RE = re.compile(
        r'('
        r'(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*'
        r'[\s,]+)?'
        r'(?:19|20)\d{2}'
        r'(?:\s*[–—\-\/to]+\s*'
        r'(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*'
        r'[\s,]+)?'
        r'(?:(?:19|20)\d{2}|present|current|ongoing))?'
        r')',
        re.IGNORECASE
    )

    def has_date(line: str) -> bool:
        return bool(DATE_RE.search(line))

    def get_date_str(line: str) -> str:
        m = DATE_RE.search(line)
        return m.group(0).strip() if m else ""

    def strip_date(line: str) -> str:
        return DATE_RE.sub("", line).strip(" ,–—:-")

    # ── Step 3: Filter out pure description lines ──
    def is_description_line(line: str) -> bool:
        # Starts with bullet
        if line[:1] in ("•", "-", "*", "–", "·", "▪", "○"):
            return True
        words = line.split()
        # Long line with no date = likely sentence/description
        if len(words) > 10 and not has_date(line):
            return True
        # Starts with lowercase = likely sentence fragment
        if words and words[0][0].islower():
            return True
        return False

    clean_lines = [l for l in exp_lines if not is_description_line(l)]

    # ── Step 4: Group lines into entries ──
    # Strategy: date-anchored entry pulls in preceding line (company)
    # and following lines (title, location, description)
    experiences = []
    used_idxs = set()

    for i, line in enumerate(clean_lines):
        if i in used_idxs:
            continue

        if has_date(line):
            date_str = get_date_str(line)
            line_no_date = strip_date(line)

            entry = {
                "title": "",
                "company": "",
                "duration": date_str,
                "description": "",
            }
            used_idxs.add(i)

            # If current line has non-date text, it might be company or title
            if line_no_date:
                entry["company"] = line_no_date

            # Look BACKWARD for company name (line just before)
            if i > 0 and (i - 1) not in used_idxs:
                prev = clean_lines[i - 1]
                if not has_date(prev) and not is_description_line(prev):
                    if not entry["company"]:
                        entry["company"] = prev
                    else:
                        entry["title"] = entry["company"]
                        entry["company"] = prev
                    used_idxs.add(i - 1)

            # Look FORWARD for title and description
            for j in range(i + 1, min(i + 4, len(clean_lines))):
                if j in used_idxs:
                    continue
                nxt = clean_lines[j]
                if has_date(nxt):
                    break  # next entry starts
                if is_description_line(nxt):
                    continue

                word_count = len(nxt.split())
                # Short line = job title; longer = description
                if not entry["title"] and word_count <= 8:
                    entry["title"] = nxt
                    used_idxs.add(j)
                elif word_count <= 15:
                    entry["description"] = nxt
                    used_idxs.add(j)
                    break

            # Only add if it has company or title
            if entry["company"] or entry["title"]:
                experiences.append(entry)

    return experiences[:5]


def extract_education(text: str) -> list:
    """
    Dynamically extract education entries from any resume.
    Uses only structural patterns — no hardcoded institution or degree names.

    Grouping logic:
    - A line containing a 4-digit year anchors a new entry
    - Lines immediately before/after that anchor (within the
      education section) are grouped with it
    - Bullet points and long descriptive sentences are excluded
    - Works on any resume regardless of institution or degree names
    """
    if not text:
        return []

    lines = text.split("\n")
    stripped_lines = [l.strip() for l in lines]

    # Generic section keywords — never hardcode specific schools/degrees
    EDU_TERMS = {"education", "academic", "qualification", "schooling"}
    END_TERMS = {
        "experience", "employment", "skills", "projects",
        "certifications", "certificate", "achievements",
        "publications", "internship", "awards", "training",
    }

    # ── Step 1: Find education section boundaries ──
    start_idx = None
    end_idx = len(stripped_lines)

    for i, line in enumerate(stripped_lines):
        line_lower = line.lower()
        word_count = len(line.split())

        # Section start: line containing generic edu term at START
        if start_idx is None:
            if any(line_lower.startswith(term) for term in EDU_TERMS):
                start_idx = i + 1
            # Alternative: line contains edu term as standalone word
            elif any(f" {term} " in f" {line_lower} " for term in EDU_TERMS):
                start_idx = i + 1

        # Section end: line containing end term (any length)
        elif start_idx is not None:
            if any(term in line_lower for term in END_TERMS):
                end_idx = i
                break

    if start_idx is None:
        return []

    edu_lines = [l for l in stripped_lines[start_idx:end_idx] if l]

    # ── Step 2: Define what a "description line" looks like ──
    # These are lines we want to SKIP — they are sentences,
    # not structured education data
    def is_description_line(line: str) -> bool:
        # Starts with a bullet character
        if line[:1] in ("•", "-", "*", "–", "·", "▪", "○"):
            return True
        
        words = line.split()
        line_lower = line.lower()
        
        # Long line with no year = likely a sentence/description
        if len(words) > 10 and not re.search(r'\b(19|20)\d{2}\b', line):
            return True
        
        # Contains a lowercase verb at the start = sentence fragment
        if words and words[0][0].islower():
            return True
        
        # Contains keywords indicating description/project/achievement lines
        desc_keywords = {
            'visualized', 'insights', 'charts', 'graphs', 'developed', 
            'created', 'built', 'implemented', 'designed', 'real-world',
            'datasets', 'project', 'achievement', 'course', 'subject',
            'using', 'with', 'for', 'till', 'until', 'based', 'focused',
            'involved', 'worked', 'led', 'managed', 'coordinated'
        }
        for keyword in desc_keywords:
            if keyword in line_lower:
                return True
        
        return False

    # ── Step 3: Year extraction helpers ──
    # Matches: "2023", "2023-2027", "Aug 2023 – May 2027",
    #          "2023 – Present", "2021 – 2023" etc.
    YEAR_RE = re.compile(
        r'('
        r'(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*'
        r'[\s,]+)?'
        r'(?:19|20)\d{2}'
        r'(?:\s*[–—\-\/to]+\s*'
        r'(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*'
        r'[\s,]+)?'
        r'(?:(?:19|20)\d{2}|present|current|ongoing))?'
        r')',
        re.IGNORECASE
    )

    def has_year(line: str) -> bool:
        return bool(YEAR_RE.search(line))

    def get_year_str(line: str) -> str:
        m = YEAR_RE.search(line)
        return m.group(0).strip() if m else ""

    def strip_year(line: str) -> str:
        return YEAR_RE.sub("", line).strip(" ,–—:-")

    def looks_like_next_record_start(line: str) -> bool:
        """Heuristic: title-cased, comma-separated short lines are likely new institution rows."""
        if not line or has_year(line):
            return False
        if "," not in line:
            return False
        if any(ch.isdigit() for ch in line):
            return False

        words = [w for w in line.replace(",", " ").split() if any(c.isalpha() for c in w)]
        if len(words) < 2 or len(words) > 8:
            return False

        title_like = sum(1 for w in words if w[:1].isupper() or w.isupper())
        return (title_like / len(words)) >= 0.7

    # ── Step 4: Group lines into entries ──
    # Strategy:
    # - Scan lines; when a line with a year is found, it anchors
    #   an entry together with the line immediately before it
    #   (institution name) and the lines immediately after it
    #   (degree, location — if they are short and non-descriptive)
    # - This works because education sections universally follow
    #   the pattern: Institution → Degree → Date → (Location)

    clean_lines = [l for l in edu_lines if not is_description_line(l)]

    entries = []
    used_idxs = set()

    for i, line in enumerate(clean_lines):
        if i in used_idxs:
            continue

        if has_year(line):
            year_str = get_year_str(line)
            line_no_yr = strip_year(line)

            entry = {
                "institution": "",
                "degree": "",
                "year": year_str,
                "location": "",
            }
            used_idxs.add(i)

            # The line itself may contain institution or degree info
            if line_no_yr:
                entry["institution"] = line_no_yr

            # Look BACKWARD for institution name (line just before)
            if i > 0 and (i - 1) not in used_idxs:
                prev = clean_lines[i - 1]
                if not has_year(prev) and not is_description_line(prev):
                    if not entry["institution"]:
                        entry["institution"] = prev
                    else:
                        entry["degree"] = entry["institution"]
                        entry["institution"] = prev
                    used_idxs.add(i - 1)

            # Look FORWARD for degree / location (lines just after)
            for j in range(i + 1, min(i + 3, len(clean_lines))):
                if j in used_idxs:
                    continue
                nxt = clean_lines[j]
                if has_year(nxt):
                    break  # next entry starts
                if is_description_line(nxt):
                    continue
                if looks_like_next_record_start(nxt):
                    break
                # Short line = location; medium line = degree
                if not entry["degree"] and len(nxt.split()) > 2:
                    entry["degree"] = nxt
                    used_idxs.add(j)
                elif not entry["location"] and len(nxt.split()) <= 6:
                    entry["location"] = nxt
                    used_idxs.add(j)

            # Only add entry if it has at least institution or degree
            if entry["institution"] or entry["degree"]:
                entries.append(entry)

    return entries[:6]
