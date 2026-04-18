# Resume Analyzer V2 - Project Summary

## Current Status

- App type: Streamlit web app
- Entry point: streamlit_app.py
- Core analysis services: implemented under app/services
- Docs updated to match implemented code only

## Implemented Architecture

### UI Layer

- streamlit_app.py
   - Upload resume (PDF, DOCX, TXT)
   - Optional job description matching
   - Four result tabs:
      - ATS Score
      - Entity Extraction
      - Job Match
      - Suggestions
   - Plotly charts (gauge, radar, bar)
   - Custom CSS-based styling in Streamlit markdown

### Service Layer

- app/services/parser.py
   - parse_pdf with fallbacks: pdfplumber, pdfminer, PyPDF2
   - parse_docx with paragraph, table, header/footer, and hyperlink handling
   - parse_txt text parsing and normalization

- app/services/hf_client.py
   - Hugging Face API client with retry and timeout handling
   - Contact extraction via regex and heuristics
   - Skills extraction via NER with fallback keyword extraction
   - Job similarity scoring with fallback overlap scoring

- app/services/ats_scorer.py
   - ATS score calculation (0-100)
   - 6 scoring categories:
      - contact_info (20)
      - skills_section (20)
      - education_section (15)
      - experience_section (15)
      - action_verbs_keywords (20)
      - resume_length (10)
   - Suggestions and missing-sections output

- app/services/experience_extractor.py
   - Structured experience extraction
   - Structured education extraction
   - Fallback extraction helpers

- app/services/matcher.py
   - Resume-to-job matching wrapper
   - Feedback text generation by match score band

- app/services/analytics.py
   - DataFrame construction and NumPy metrics
   - Matplotlib chart generation utilities

### Utility Layer

- app/utils/helpers.py
   - File validation (extensions + size)
   - Text cleanup helpers
   - Keyword and skill cleanup
   - Action verb and word count helpers

## Implemented Feature Set

- Resume upload and parsing
- ATS score and section-wise breakdown
- Entity extraction:
   - Name
   - Email
   - Phone
   - Skills
   - Education
   - Experience
- Optional job description match:
   - Match score
   - Matched keywords
   - Missing keywords
- Recommendation and improvement suggestions

## Runtime and Dependencies

- Python dependencies are defined in requirements.txt
- Primary runtime libraries used in the app:
   - streamlit
   - requests
   - python-dotenv
   - PyPDF2
   - pdfplumber
   - pdfminer.six
   - python-docx
   - numpy
   - pandas
   - matplotlib
   - plotly

## Current Repository Notes

- app/routes is present but currently empty
- app/templates is present but currently empty
- static folders exist and are available
- No run.py entry point in current root
- No tests directory in current root

## Deployment Configuration Present

- Procfile:
   - streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
- vercel.json:
   - Uses @vercel/python
   - Routes requests to streamlit_app.py

## Command To Run Locally

```bash
streamlit run streamlit_app.py
```
