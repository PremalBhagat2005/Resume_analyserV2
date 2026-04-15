import os
import tempfile
from flask import Blueprint, request, render_template, jsonify
from werkzeug.utils import secure_filename

from app.utils.helpers import validate_file, extract_skills_from_keywords, clean_keywords
from app.services.parser import parse_resume
from app.services.hf_client import extract_entities
from app.services.ats_scorer import calculate_ats_score
from app.services.matcher import match_resume_to_job
from app.services.experience_extractor import extract_work_experience
from app.services.analytics import ResumeAnalytics

analyse_bp = Blueprint('analyse', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')


@analyse_bp.route("/analyse", methods=["POST"])
def analyse():
    """
    Process uploaded resume and calculate ATS score and job match.
    
    Form data:
        - file: Resume file (PDF, DOCX, TXT)
        - job_description: (optional) Job description text
    
    Returns:
        Rendered result.html with analysis results
    """
    try:
        # Validate file upload
        if 'file' not in request.files:
            return render_template('result.html', error="No file provided")
        
        file = request.files['file']
        is_valid, error_msg = validate_file(file)
        
        if not is_valid:
            return render_template('result.html', error=error_msg)
        
        # Get optional job description
        job_description = request.form.get('job_description', '').strip()
        
        # Parse resume
        try:
            resume_text = parse_resume(file)
            
            if not resume_text or len(resume_text) < 50:
                return render_template('result.html', error="Resume text is too short or empty")
        
        except ValueError as e:
            return render_template('result.html', error=str(e))
        
        # Extract entities using Hugging Face NER
        try:
            extracted_entities = extract_entities(resume_text)
        except Exception as e:
            extracted_entities = {
                "name": None,
                "email": None,
                "phone": None,
                "skills": [],
                "education": [],
                "experience": []
            }
        
        # Calculate ATS score
        ats_result = calculate_ats_score(resume_text, extracted_entities)
        
        # Extract skills and clean keywords
        extracted_keywords = ats_result['extracted_keywords']
        extracted_skills = extract_skills_from_keywords(extracted_keywords)
        extracted_keywords = clean_keywords(extracted_keywords)
        
        # Match with job description if provided
        match_result = None
        if job_description and len(job_description) > 20:
            try:
                match_result = match_resume_to_job(resume_text, job_description)
            except Exception as e:
                print(f"Job matching error: {e}")
                match_result = None
        
        # Extract work experience
        work_experience = extract_work_experience(resume_text)
        
        # Initialize analytics and generate visualizations
        try:
            analytics = ResumeAnalytics()
            
            # Build dataframe for data structuring
            results_df = analytics.build_dataframe(
                ats_result=ats_result,
                match_result=match_result,
                extracted_entities=extracted_entities
            )
            
            # Generate charts
            chart_paths = analytics.generate_charts(
                ats_result=ats_result,
                match_result=match_result,
                extracted_entities=extracted_entities
            )
        except Exception as e:
            print(f"Analytics error: {e}")
            chart_paths = {}
        
        # Prepare context for template
        context = {
            'file_name': secure_filename(file.filename),
            'ats_score': ats_result['score'],
            'ats_breakdown': ats_result['breakdown'],
            'keywords': extracted_keywords,
            'extracted_skills': extracted_skills,
            'missing_sections': ats_result['missing_sections'],
            'suggestions': ats_result['suggestions'],
            'word_count': ats_result['word_count'],
            'extracted_entities': extracted_entities,
            'match_result': match_result,
            'has_job_description': bool(job_description),
            'work_experience': work_experience,
            'chart_paths': chart_paths
        }
        
        return render_template('result.html', **context)
    
    except Exception as e:
        print(f"Analysis error: {e}")
        return render_template('result.html', error=f"An error occurred: {str(e)}")
