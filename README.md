# Resume Analyser

An AI-powered web app that analyzes resumes and scores them based on ATS optimization. Upload your resume and get an instant score with actionable feedback.

## What It Does

- **ATS Scoring (0-100)** - Evaluates your resume against 6 key factors
- **Entity Extraction** - Automatically pulls out contact info, skills, education, and experience
- **Job Matching** - Compares your resume to job descriptions and shows matching/missing keywords
- **Dark Theme UI** - Modern, responsive design with instant visual feedback

## Quick Start

### Prerequisites
- Python 3.8+
- Hugging Face API key (free at [huggingface.co](https://huggingface.co))

### Setup

1. Clone and enter directory:
   ```bash
   git clone <repository-url>
   cd resume-analyser
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```env
   HF_API_KEY=your_hf_token_here
   FLASK_ENV=development
   ```

5. Run:
   ```bash
   python run.py
   ```

   Open `http://localhost:5000`

## How Scoring Works

| Factor | Points | What We Check |
|--------|--------|---------------|
| Contact Info | 20 | Name, email, phone |
| Skills Section | 20 | Has dedicated skills with 3+ items |
| Education | 15 | Degree or certification |
| Experience | 15 | Work history present |
| Action Verbs | 20 | Uses power words (managed, developed, etc.) |
| Length | 10 | Between 300-800 words |

## Tech Stack

- **Backend**: Flask, Python
- **Parsing**: PyPDF2, python-docx
- **AI Models**: Hugging Face (NER + semantic similarity)
- **Frontend**: HTML, CSS (no JavaScript)
- **Data Analysis**: NumPy, Pandas, Matplotlib

## Project Structure

```
app/
├── routes/          # Flask routes
├── services/        # Core logic (parsing, scoring, analysis)
├── utils/           # Helper functions
├── templates/       # HTML pages
└── static/          # CSS and uploaded files

requirements.txt     # Dependencies
run.py              # Start here
```

## Deployment

### Vercel

1. Push to GitHub
2. Create new project on [vercel.com](https://vercel.com)
3. Add `HF_API_KEY` environment variable
4. Deploy

## Troubleshooting

**"Model is loading" error**
- First request takes 30-60 seconds
- App automatically retries
- It's normal

**File upload fails**
- Max file size: 5MB
- Supported: PDF, DOCX, TXT
- Check file isn't corrupted

**API key error**
- Verify key in `.env`
- Regenerate at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

## Security Notes

- `.env` files never committed (check `.gitignore`)
- Uploaded files deleted after analysis
- No data stored permanently
- Input validation on all uploads

## Future Ideas

- User dashboard with analysis history
- Resume templates
- Multiple resume comparison
- Cover letter analysis

## License

MIT - use freely for personal and commercial projects
