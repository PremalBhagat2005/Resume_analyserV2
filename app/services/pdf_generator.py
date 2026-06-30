import os
import tempfile
import uuid
from fpdf import FPDF
from typing import Dict, Any

class ATSResumePDF(FPDF):
    def header(self):
        # No header to keep it as clean as possible for ATS
        pass

    def footer(self):
        pass

def sanitize(text: Any) -> str:
    if not text:
        return ""
    text = str(text)
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': "-", '\u2014': "-", '\u2026': "...", '\u2022': "-",
        '\t': "    "
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def generate_ats_pdf(data: Dict[str, Any]) -> str:
    """
    Generates a clean, single-column ATS-friendly PDF.
    Returns the absolute file path to the generated PDF.
    """
    pdf = ATSResumePDF()
    pdf.add_page()
    pdf.set_margins(left=12.7, top=12.7, right=12.7)
    pdf.set_auto_page_break(auto=True, margin=12.7)

    # --- Header (Contact Info) ---
    pdf.set_font("Arial", "B", 16)
    name = sanitize(data.get("name", "Applicant Name") or "Applicant Name")
    pdf.cell(0, 8, name, ln=True, align="C")

    pdf.set_font("Arial", "", 10)
    contact_parts = []
    if data.get("email"):
        contact_parts.append(sanitize(data.get("email")))
    if data.get("phone"):
        contact_parts.append(sanitize(data.get("phone")))
    if data.get("linkedin"):
        contact_parts.append(sanitize(data.get("linkedin")))
    if data.get("github"):
        contact_parts.append(sanitize(data.get("github")))
    
    if contact_parts:
        contact_str = " | ".join(contact_parts)
        pdf.multi_cell(0, 5, contact_str, align="C")
    pdf.ln(3)

    def section_header(title):
        pdf.ln(3)
        pdf.set_font("Arial", "B", 11)
        # We use a simple uppercase header with an underline simulation
        pdf.cell(0, 5, sanitize(title).upper(), ln=True, border="B")
        pdf.ln(2)

    # --- Summary ---
    summary = data.get("summary")
    if summary:
        section_header("Professional Summary")
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 4.5, sanitize(summary))

    # --- Technical Skills ---
    skills = data.get("skills", [])
    if skills:
        section_header("Technical Skills")
        pdf.set_font("Arial", "", 10)
        skills_str = sanitize(", ".join(skills))
        pdf.multi_cell(0, 4.5, skills_str)

    # --- Work Experience ---
    experience = data.get("experience", [])
    if experience:
        section_header("Work Experience")
        for exp in experience:
            pdf.set_font("Arial", "B", 11)
            title = exp.get("title", "")
            company = exp.get("company", "")
            
            # Title & Company
            header_str = sanitize(title)
            if company:
                header_str += f" at {sanitize(company)}"
            
            # Truncate header if it's too long to avoid overlapping the date
            if pdf.get_string_width(header_str) > 130:
                while pdf.get_string_width(header_str + "...") > 130 and len(header_str) > 0:
                    header_str = header_str[:-1]
                header_str += "..."
                    
            pdf.cell(140, 6, header_str, ln=False)
            
            # Duration (right aligned)
            duration = sanitize(exp.get("duration", ""))
            pdf.set_font("Arial", "", 10)
            if duration:
                pdf.cell(0, 5, duration, ln=True, align="R")
            else:
                pdf.ln(5)
            
            # Bullets
            pdf.set_font("Arial", "", 10)
            desc = exp.get("description", [])
            if isinstance(desc, str):
                desc = [desc]
            for bullet in desc:
                # Use a standard bullet character
                bullet_text = sanitize(bullet.strip())
                if bullet_text:
                    pdf.set_x(16)
                    pdf.multi_cell(0, 4.5, f"- {bullet_text}")
            pdf.ln(1)

    # --- Projects ---
    projects = data.get("projects", [])
    if projects:
        section_header("Projects")
        for proj in projects:
            pdf.set_font("Arial", "B", 11)
            title = sanitize(proj.get("title", ""))
            pdf.cell(0, 5, title, ln=True)
            
            pdf.set_font("Arial", "", 10)
            desc = proj.get("description", [])
            if isinstance(desc, str):
                desc = [desc]
            for bullet in desc:
                bullet_text = sanitize(bullet.strip())
                if bullet_text:
                    pdf.set_x(16)
                    pdf.multi_cell(0, 4.5, f"- {bullet_text}")
            pdf.ln(1)

    # --- Education ---
    education = data.get("education", [])
    if education:
        section_header("Education")
        for edu in education:
            pdf.set_font("Arial", "B", 11)
            inst = sanitize(edu.get("institution", ""))
            deg = sanitize(edu.get("degree", ""))
            
            header_str = inst
            if deg:
                header_str += f", {deg}"
                
            # Truncate header if it's too long to avoid overlapping the year
            if pdf.get_string_width(header_str) > 130:
                while pdf.get_string_width(header_str + "...") > 130 and len(header_str) > 0:
                    header_str = header_str[:-1]
                header_str += "..."
                    
            pdf.cell(140, 6, header_str, ln=False)
            
            year = sanitize(edu.get("year", ""))
            pdf.set_font("Arial", "", 10)
            if year:
                pdf.cell(0, 5, year, ln=True, align="R")
            else:
                pdf.ln(5)
            
            loc = sanitize(edu.get("location", ""))
            if loc:
                pdf.cell(0, 4.5, loc, ln=True)
            pdf.ln(1)
            
    # --- Certificates ---
    certificates = data.get("certificates", [])
    if certificates:
        section_header("Certificates")
        pdf.set_font("Arial", "", 10)
        for cert in certificates:
            pdf.set_x(16)
            pdf.multi_cell(0, 4.5, f"- {sanitize(cert)}")

    # Generate output
    output_path = os.path.join(tempfile.gettempdir(), f"ATS_Resume_{uuid.uuid4().hex}.pdf")
    pdf.output(output_path)
    return output_path
