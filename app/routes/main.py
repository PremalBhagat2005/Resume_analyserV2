from flask import (
    Blueprint, render_template, request, session, redirect, url_for
)
import os
import tempfile
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from concurrent.futures import ThreadPoolExecutor

from app.services.parser import extract_text
from app.services.hf_client import call_ner_model, extract_name_fallback
from app.services.ats_scorer import calculate_ats_score
from app.services.matcher import match_resume_to_job
from app.services.experience_extractor import (
    extract_work_experience, extract_education
)
from app.services.formatting_scorer import score_formatting
from app.services.readability_scorer import score_readability
from app.services.industry_detector import detect_industry
from app.services.section_feedback import generate_section_feedback
from app.services.keyword_gap import categorise_keyword_gaps
from app.services.role_ats_scorer import score_role_specific_ats
from app.utils.helpers import extract_skills_from_keywords, clean_keywords
from app.models.db import (
    create_user,
    get_user_by_email,
    save_analysis,
    get_user_analyses,
    is_db_available,
)

main_bp = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5MB


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    if not is_db_available():
        return render_template(
            "signup.html",
            error="Database is not configured. Set MONGO_URI first.",
        )

    full_name = request.form.get("fullname", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    accepted_terms = request.form.get("terms")

    if not full_name or not email or not password:
        return render_template("signup.html", error="All fields are required.")

    if len(password) < 8:
        return render_template(
            "signup.html",
            error="Password must be at least 8 characters long.",
        )

    if password != confirm_password:
        return render_template("signup.html", error="Passwords do not match.")

    if not accepted_terms:
        return render_template("signup.html", error="Please accept terms to continue.")

    user_doc, create_error = create_user(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password),
    )
    if create_error:
        return render_template("signup.html", error=create_error)

    session["user_id"] = str(user_doc["_id"])
    session["user_name"] = user_doc.get("full_name", "")
    session["user_email"] = user_doc.get("email", "")
    return redirect(url_for("main.index"))


@main_bp.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        return render_template("signin.html")

    if not is_db_available():
        return render_template(
            "signin.html",
            error="Database is not configured. Set MONGO_URI first.",
        )

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("signin.html", error="Email and password are required.")

    user_doc = get_user_by_email(email)
    if not user_doc:
        return render_template("signin.html", error="No account found for this email.")

    if not check_password_hash(user_doc.get("password_hash", ""), password):
        return render_template("signin.html", error="Incorrect password.")

    session["user_id"] = str(user_doc["_id"])
    session["user_name"] = user_doc.get("full_name", "")
    session["user_email"] = user_doc.get("email", "")
    return redirect(url_for("main.index"))


@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))


@main_bp.route("/history")
def history():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("main.signin"))

    analyses = get_user_analyses(user_id=user_id, limit=30)
    return render_template("history.html", analyses=analyses)


@main_bp.route("/analyse", methods=["POST"])
def analyse():

    # Validate upload
    if "resume" not in request.files:
        return render_template("index.html",
                               error="No file was uploaded.")

    file = request.files["resume"]

    if not file or file.filename == "":
        return render_template("index.html",
                               error="Please select a file.")

    if not allowed_file(file.filename):
        return render_template(
            "index.html",
            error="Unsupported file type. Upload a PDF, DOCX, or TXT."
        )

    # Read once to check size before saving
    file_bytes = file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        return render_template("index.html",
                               error="File exceeds 5MB limit.")

    job_description = request.form.get("job_description", "").strip()

    # Save to temp file
    filename_safe = secure_filename(file.filename)
    suffix = "." + filename_safe.rsplit(".", 1)[1].lower()
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix
    )
    tmp.write(file_bytes)
    tmp.flush()
    tmp.close()
    tmp_path = tmp.name

    try:
        # Parse text (uses pdfplumber->pdfminer->PyPDF2 chain)
        resume_text = extract_text(tmp_path)

        if not resume_text or len(resume_text.strip()) < 50:
            return render_template(
                "index.html",
                error=(
                    "Could not extract readable text from this file. "
                    "Try saving as a different format."
                )
            )

        # Step 2 + 3: Run entity extraction and experience extraction in parallel
        # extract_entities hits HF API (slow)
        # extract_education is regex-based (fast) and included in experience extraction
        # Running together saves ~2-3 seconds
        ner_result = None
        work_experience = None
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            ner_future = executor.submit(call_ner_model, resume_text)
            experience_future = executor.submit(extract_work_experience, resume_text)
            
            try:
                ner_result = ner_future.result(timeout=90)
            except Exception as e:
                print(f"[Analyse] NER extraction failed: {e}")
                ner_result = {"name": None, "email": "", "phone": "", "keywords": []}
            
            try:
                work_experience = experience_future.result(timeout=30)
            except Exception as e:
                print(f"[Analyse] Experience extraction failed: {e}")
                work_experience = []
        
        name = ner_result.get("name")
        if not name or str(name).strip().lower() == "not detected":
            name = extract_name_fallback(resume_text)
        email = ner_result.get("email", "")
        phone = ner_result.get("phone", "")
        raw_keywords = ner_result.get("keywords", [])

        # Skills and keyword cleanup
        extracted_skills = extract_skills_from_keywords(raw_keywords)
        extracted_keywords = clean_keywords(raw_keywords)

        # Education extraction (can run independently)
        education = extract_education(resume_text)

        # ATS scoring (6 sections, total 100)
        ats_entities = {
            "name": name,
            "email": email,
            "phone": phone,
            "skills": extracted_skills,
            "experience": work_experience,
            "education": education,
        }
        ats_result = calculate_ats_score(resume_text, entities=ats_entities)
        score = ats_result.get("score", 0)
        breakdown = ats_result.get("breakdown", {})
        suggestions = ats_result.get("suggestions", [])

        # Job match analysis
        job_match = None
        if job_description:
            job_match = match_resume_to_job(
                resume_text, job_description
            )

        # Restore analytics chart generation with graceful fallback.
        chart_paths = {}
        try:
            from app.services.analytics import create_analytics
            analytics = create_analytics()
            chart_paths = analytics.generate_charts(
                ats_result=ats_result,
                match_result=job_match,
                extracted_entities=ats_entities,
            )
        except Exception:
            chart_paths = {}

        # Score band
        if score >= 80:
            score_band, score_class = "Excellent", "excellent"
        elif score >= 60:
            score_band, score_class = "Good", "good"
        elif score >= 40:
            score_band, score_class = "Needs Work", "fair"
        else:
            score_band, score_class = "Poor", "poor"

        # Humanize breakdown keys
        breakdown_labels = {
            "contact_info": "Contact Information",
            "contact": "Contact Information",
            "skills_section": "Skills",
            "skills": "Skills",
            "education_section": "Education",
            "education": "Education",
            "experience_section": "Work Experience",
            "experience": "Work Experience",
            "action_verbs": "Action Verbs & Keywords",
            "keywords": "Action Verbs & Keywords",
            "action_keywords": "Action Verbs & Keywords",
            "length": "Resume Length",
            "resume_length": "Resume Length",
        }
        breakdown_display = {
            breakdown_labels.get(
                k.lower(), k.replace("_", " ").title()
            ): v
            for k, v in breakdown.items()
        }

        word_count = len(resume_text.split())

        # New analysis features
        formatting_result = score_formatting(resume_text)
        readability_result = score_readability(resume_text)
        industry_result = detect_industry(resume_text)

        section_feedback = generate_section_feedback(
            text=resume_text,
            ats_breakdown=breakdown,
            work_experience=work_experience,
            education=education,
            extracted_skills=extracted_skills,
        )

        # Role-specific ATS (only if JD provided)
        role_ats = None
        if job_description:
            role_ats = score_role_specific_ats(
                resume_text=resume_text,
                job_description=job_description,
                base_ats_score=score,
            )

        # Keyword gap categories (only if JD + job_match)
        keyword_gaps = None
        if job_match and job_description:
            keyword_gaps = categorise_keyword_gaps(
                resume_text=resume_text,
                job_description=job_description,
                current_missing=job_match.get("missing_keywords", []),
            )

    finally:
        # Always delete temp file; never persist user data.
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if session.get("user_id") and is_db_available():
        save_analysis(
            user_id=session.get("user_id"),
            analysis_payload={
                "filename": filename_safe,
                "score": score,
                "score_band": score_band,
                "score_class": score_class,
                "word_count": word_count,
                "job_description_provided": bool(job_description),
                "match_score": (
                    (job_match or {}).get("match_score") if job_match else None
                ),
            },
        )

    return render_template(
        "result.html",
        filename=filename_safe,
        score=score,
        score_band=score_band,
        score_class=score_class,
        breakdown=breakdown_display,
        suggestions=suggestions,
        name=name,
        email=email,
        phone=phone,
        extracted_skills=extracted_skills,
        extracted_keywords=extracted_keywords,
        work_experience=work_experience,
        education=education,
        job_match=job_match,
        chart_paths=chart_paths,
        word_count=word_count,
        job_description=job_description,
        formatting_result=formatting_result,
        readability_result=readability_result,
        industry_result=industry_result,
        section_feedback=section_feedback,
        role_ats=role_ats,
        keyword_gaps=keyword_gaps,
    )