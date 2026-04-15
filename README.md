# Resume Analyser - AI-Powered Resume Optimization

A modern web application that analyzes resumes using AI, calculates ATS (Applicant Tracking System) scores, extracts key information, and matches resumes against job descriptions.

## Features

✨ **ATS Score Calculation** (0-100)
- Contact information validation (20pts)
- Skills section detection (20pts)
- Education section detection (15pts)
- Experience section detection (15pts)
- Action verbs and keywords analysis (20pts)
- Optimal resume length check (10pts)

🔍 **Entity Extraction**
- Automatic name, email, and phone detection
- Skills extraction
- Education details
- Experience highlights
- Using Hugging Face NER model (yashpwr/resume-ner-bert-v2)

⚡ **Job Description Matching**
- Semantic similarity scoring (0-100%)
- Matched keywords identification
- Missing keywords suggestions
- Strength areas highlighting
- Improvement areas recommendations
- Using Hugging Face model (anass1209/resume-job-matcher-all-MiniLM-L6-v2)

📊 **Smart Analysis**
- Detailed score breakdown with visual indicators
- Actionable improvement suggestions
- Support for PDF, DOCX, and TXT files
- File size limit: 5MB

🎨 **Modern UI**
- Dark theme design (#0a0a0f background)
- Electric teal accents (#00d4aa)
- Circular score gauges
- Pure CSS (no JavaScript)
- Fully responsive design
- Smooth animations and transitions

## Tech Stack

**Backend:**
- Python 3.8+
- Flask 2.3.3
- PyPDF2 (PDF parsing)
- python-docx (DOCX parsing)
- requests (API calls)

**Frontend:**
- HTML5 (no JavaScript)
- CSS3 (modern styling)
- Google Fonts (DM Mono, Outfit, Space Mono)

**API:**
- Hugging Face Inference API
- NER model: yashpwr/resume-ner-bert-v2
- Similarity model: anass1209/resume-job-matcher-all-MiniLM-L6-v2

**Deployment:**
- Vercel (with Python support)
- Gunicorn WSGI server

## Project Structure

```
resume-analyser/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes/
│   │   ├── main.py              # Landing page route (GET /)
│   │   └── analyse.py           # Analysis route (POST /analyse)
│   ├── services/
│   │   ├── parser.py            # PDF/DOCX/TXT file parsing
│   │   ├── hf_client.py         # Hugging Face API integration
│   │   ├── ats_scorer.py        # ATS scoring logic
│   │   └── matcher.py           # Job description matching
│   ├── utils/
│   │   └── helpers.py           # Utility functions
│   ├── models/
│   │   └── db.py                # MongoDB integration (stub)
│   ├── templates/
│   │   ├── base.html            # Base layout template
│   │   ├── index.html           # Upload form page
│   │   └── result.html          # Analysis results page
│   └── static/
│       ├── css/
│       │   └── style.css        # Main stylesheet
│       └── uploads/             # Temporary file storage
├── tests/
│   └── test_services.py         # Unit tests
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── vercel.json                 # Vercel deployment config
├── .env                        # Environment variables
├── .env.example                # Environment template
└── .gitignore                  # Git ignore rules
```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip or conda
- Hugging Face API key (get from [huggingface.co](https://huggingface.co))

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd resume-analyser
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy .env.example to .env
   cp .env.example .env
   
   # Update .env with your values
   # Replace YOUR_API_KEY with actual Hugging Face API key
   ```

5. **Run the application:**
   ```bash
   python run.py
   ```

   The app will be available at `http://localhost:5000`

## Environment Variables

Create a `.env` file in the project root:

```env
HF_API_KEY=your_hugging_face_api_key_here
FLASK_ENV=development
```

**Required:**
- `HF_API_KEY`: Your Hugging Face API token
- Get it from: https://huggingface.co/settings/tokens

**Optional:**
- `FLASK_ENV`: Set to `production` for deployment

## API Usage

### Upload and Analyze Resume

**Endpoint:** `POST /analyse`

**Form Data:**
- `file` (required): Resume file (PDF, DOCX, or TXT, max 5MB)
- `job_description` (optional): Job description text for matching

**Response:**
- Returns HTML page with analysis results
- Includes ATS score, entity extractions, keywords, and suggestions
- If job description provided, includes match score and recommendations

## Hugging Face Models

### NER Model (resume-ner-bert-v2)
- **Purpose:** Extract named entities from resume text
- **Output:** Name, email, phone, skills, education, experience
- **Link:** https://huggingface.co/yashpwr/resume-ner-bert-v2

### Similarity Model (resume-job-matcher-all-MiniLM-L6-v2)
- **Purpose:** Calculate semantic similarity between resume and job description
- **Output:** Similarity score (0-1, scaled to 0-100%)
- **Link:** https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

## ATS Score Breakdown

| Component | Points | Criteria |
|-----------|--------|----------|
| Contact Info | 20 | Name, email, phone presence |
| Skills Section | 20 | Dedicated skills section with 3+ skills |
| Education | 15 | Education/degree information |
| Experience | 15 | Work history and roles |
| Action Verbs | 20 | 10+ action verbs (managed, developed, etc.) |
| Resume Length | 10 | 300-800 word count |
| **Total** | **100** | |

## Design System

### Colors
- **Primary Background:** #0a0a0f
- **Secondary Background:** #13131a
- **Tertiary Background:** #1a1a24
- **Accent Primary:** #00d4aa (electric teal)
- **Accent Secondary:** #00b896
- **Success:** #00d4aa
- **Warning:** #ffb800
- **Error:** #ff4757
- **Text Primary:** #ffffff
- **Text Secondary:** #a8a8b8

### Typography
- **Body Font:** Outfit (400, 500, 600, 700)
- **Mono Font:** DM Mono (400, 500)
- **Mono Alt:** Space Mono (400, 700)

## Deployment

### Deploy to Vercel

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Set environment variables in Vercel dashboard

3. **Configure environment:**
   - Add `HF_API_KEY` with your token
   - Vercel will automatically use `vercel.json` config

4. **Deploy:**
   - Vercel will automatically deploy on push to main branch

## Testing

Run tests using pytest:

```bash
# Install test dependencies (add pytest to requirements.txt)
pip install pytest

# Run tests
pytest tests/ -v
```

## API Rate Limits

The Hugging Face Inference API has usage limits:
- Free tier: Limited inference calls
- Pro tier: Higher limits available

If you encounter 503 (Service Unavailable) errors, the model is being loaded. The app includes retry logic with exponential backoff.

## Future Enhancements

- [ ] MongoDB integration for storing analysis history
- [ ] User authentication and dashboard
- [ ] Multiple resume comparison
- [ ] Resume template suggestions
- [ ] Cover letter analysis
- [ ] Interview preparation tips
- [ ] LinkedIn profile integration
- [ ] Bulk resume analysis

## Database Integration (MongoDB)

The project includes a stub for MongoDB integration. To enable:

1. **Update `.env`:**
   ```env
   MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/resume_analyser
   ```

2. **Uncomment in `app/models/db.py`:**
   - Import MongoClient
   - Implement `init_db()`, `save_analysis()`, `get_analysis_history()`

3. **Enable in `app/__init__.py`:**
   - Uncomment `init_db(app)` call

## Security Considerations

⚠️ **Important:**
- Never commit `.env` file (already in `.gitignore`)
- Uploaded files are temporary and deleted after analysis
- API tokens are secured via environment variables
- Input validation on all file uploads
- CSRF protection recommended for production

## Troubleshooting

### "Model is loading" Error
- Model is warming up on Hugging Face servers
- App automatically retries with backoff
- Usually takes 30-60 seconds on first use

### File Upload Fails
- Check file size (max 5MB)
- Verify file format (PDF, DOCX, TXT)
- Ensure file is not corrupted

### API Key Error
- Verify `HF_API_KEY` is set correctly in `.env`
- Check token hasn't expired or been revoked
- Regenerate token if needed at huggingface.co

## License

MIT License - feel free to use this project for personal and commercial use.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review code comments for implementation details

## Technical Details

### Resume Text Extraction
- **PDF:** Uses PyPDF2 library for page extraction
- **DOCX:** Uses python-docx for document parsing
- **TXT:** Direct UTF-8 text reading

### Text Processing
- Whitespace normalization
- Special character removal (preserves punctuation)
- Case-insensitive keyword matching
- Duplicate removal for keywords

### ATS Score Calculation
- Weighted point system (0-100)
- Threshold-based section detection
- Action verb counting and scoring
- Word count range validation (300-800 optimal)

### Job Matching Algorithm
- Semantic similarity using transformer models
- Token-level matching for keyword identification
- Skill extraction and comparison
- Missing keyword recommendations

## Version History

- **v1.0.0** (2026-04-14) - Initial release
  - ATS score calculation
  - Entity extraction via NER
  - Job description matching
  - Modern dark-themed UI
  - No JavaScript (pure CSS)
  - Vercel deployment ready

---

Built with ❤️ for job seekers optimizing their resumes
