# Resume Analyzer V2

Streamlit-based resume analysis app that scores ATS readiness, extracts key resume entities, and optionally compares resume content against a job description.

## Implemented Features

- ATS score from 0 to 100 with a 6-part breakdown:
  - Contact info (20)
  - Skills section (20)
  - Education section (15)
  - Experience section (15)
  - Action verbs and keywords (20)
  - Resume length (10)
- Resume parsing for PDF, DOCX, and TXT
- Contact extraction (name, email, phone) using regex and heuristics
- Skills extraction using Hugging Face NER with fallback keyword extraction
- Education and work experience extraction using structure-based parsing
- Optional job match scoring with matched and missing keywords
- Interactive Streamlit dashboard with charts and tabbed results

## Requirements

- Python 3.8+
- Pip
- Optional but recommended: Hugging Face API key

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a .env file (or copy from .env.example):

```env
HF_API_KEY=your_hugging_face_api_key_here
FLASK_ENV=development
```

Notes:
- The app uses HF inference APIs when available.
- If HF calls fail, fallback logic still runs for key parts (skills and job matching).

3. Start the app:

```bash
streamlit run streamlit_app.py
```

4. Open the local URL shown by Streamlit (default is usually http://localhost:8501).

## How To Use

1. Upload a resume file (.pdf, .docx, or .txt)
2. Optionally enable and paste a job description
3. Click Analyze Resume
4. Review four result tabs:
   - ATS Score
   - Entity Extraction
   - Job Match
   - Suggestions

## File Validation

- Supported extensions: pdf, docx, txt
- Maximum file size: 5 MB

## Current Project Structure

```text
.
|-- streamlit_app.py
|-- requirements.txt
|-- Procfile
|-- vercel.json
|-- app/
|   |-- services/
|   |   |-- parser.py
|   |   |-- hf_client.py
|   |   |-- ats_scorer.py
|   |   |-- matcher.py
|   |   |-- experience_extractor.py
|   |   `-- analytics.py
|   |-- utils/
|   |   `-- helpers.py
|   |-- routes/        (currently empty)
|   `-- templates/     (currently empty)
`-- static/
```

## Deployment Notes

- Procfile starts Streamlit with:

```text
streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

- vercel.json routes requests to streamlit_app.py using @vercel/python.

## Known Behavior

- Hugging Face model cold starts can cause temporary delays or 503 responses; retry logic is built in.
- If model/API calls fail, the app falls back to local keyword/overlap logic where implemented.

## License

MIT
