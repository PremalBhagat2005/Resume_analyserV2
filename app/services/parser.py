import io
from PyPDF2 import PdfReader
from docx import Document
from werkzeug.utils import secure_filename
from app.utils.helpers import clean_text


def parse_pdf(file):
    """
    Extract text from PDF file.
    Returns extracted text string.
    """
    try:
        pdf_reader = PdfReader(io.BytesIO(file.read()))
        text = ""
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        return clean_text(text) if text else ""
    
    except Exception as e:
        raise ValueError(f"Error parsing PDF: {str(e)}")


def parse_docx(file):
    """
    Extract text from DOCX file.
    Returns extracted text string.
    """
    try:
        doc = Document(io.BytesIO(file.read()))
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return clean_text(text) if text else ""
    
    except Exception as e:
        raise ValueError(f"Error parsing DOCX: {str(e)}")


def parse_txt(file):
    """
    Extract text from TXT file.
    Returns extracted text string.
    """
    try:
        content = file.read().decode('utf-8', errors='ignore')
        return clean_text(content) if content else ""
    
    except Exception as e:
        raise ValueError(f"Error parsing TXT: {str(e)}")


def parse_resume(file):
    """
    Parse resume file and extract text.
    Determines file type and calls appropriate parser.
    
    Args:
        file: werkzeug FileStorage object
    
    Returns:
        str: Extracted and cleaned resume text
    
    Raises:
        ValueError: If file type is not supported or parsing fails
    """
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    # Reset file pointer to beginning
    file.seek(0)
    
    if ext == 'pdf':
        return parse_pdf(file)
    elif ext == 'docx':
        return parse_docx(file)
    elif ext == 'txt':
        return parse_txt(file)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
