# Quick Start

## 1) Install

```bash
pip install -r requirements.txt
```

## 2) Configure Environment

Create a .env file in the project root:

```env
HF_API_KEY=your_hugging_face_api_key_here
FLASK_ENV=development
```

HF_API_KEY is recommended for best results with NER and similarity models.

## 3) Run

```bash
streamlit run streamlit_app.py
```

Open the URL shown in terminal (typically http://localhost:8501).

## 4) Analyze a Resume

1. Upload a PDF, DOCX, or TXT file
2. Optionally enable job description matching and paste a JD
3. Click Analyze Resume
4. Review the output tabs:
   - ATS Score
   - Entity Extraction
   - Job Match
   - Suggestions

## Supported Files

- PDF (.pdf)
- DOCX (.docx)
- TXT (.txt)
- Max size: 5 MB

## ATS Score Sections

- Contact info: 20
- Skills section: 20
- Education section: 15
- Experience section: 15
- Action verbs and keywords: 20
- Resume length: 10

## Common Issues

Model loading or temporary API error:
- Retry after a short wait
- The app includes retry and fallback logic

No/weak extraction results:
- Ensure resume has clear section headers (Skills, Education, Experience)
- Use plain, readable formatting

Upload rejected:
- Verify file type and keep size under 5 MB

## Production Command

Procfile uses:

```text
streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```
