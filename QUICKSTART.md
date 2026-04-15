# Quick Start Guide

## Get the App Running in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure API Key
Get your free Hugging Face API key:
1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Create a new token (read access is enough)
3. Add to `.env` file:
```env
HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxx
FLASK_ENV=development
```

### Step 3: Run the Application
```bash
python run.py
```

### Step 4: Open in Browser
Navigate to: **http://localhost:5000**

---

## Using the Application

### Analyze Your Resume

1. **Upload Resume**
   - Click the upload area or drag & drop
   - Supports PDF, DOCX, TXT files (max 5MB)

2. **Optional: Add Job Description**
   - Paste the job description to get job matching insights
   - Leave empty to only get ATS score

3. **Get Results**
   - ATS Score (0-100)
   - Score breakdown by category
   - Extracted contact info
   - Identified keywords
   - Missing sections
   - Improvement suggestions
   - Job match score (if job description provided)

---

## File Formats Supported

| Format | Extension | Size Limit |
|--------|-----------|-----------|
| PDF    | .pdf      | 5 MB      |
| Word   | .docx     | 5 MB      |
| Text   | .txt      | 5 MB      |

---

## Understanding Your ATS Score

### 80-100: Excellent ✅
Your resume is well-optimized. Consider small tweaks for perfection.

### 60-79: Good 👍
Your resume has solid foundations. Implement suggested improvements.

### 40-59: Fair ⚠️
Consider major revisions. Focus on missing sections and keywords.

### Below 40: Needs Work ❌
Significant improvements needed. Follow all suggestions.

---

## Common Issues

### "Model is loading" Error
**Solution:** Wait 30-60 seconds and try again. The AI model is warming up.

### File Upload Fails
**Check:**
- File is not corrupted
- File size is under 5MB
- File format is PDF, DOCX, or TXT

### API Key Error
**Solution:**
1. Verify key in `.env` file
2. Check key is not expired at huggingface.co
3. Keys start with `hf_` prefix

---

## Next Steps

### Deploy to Vercel
```bash
# 1. Push to GitHub
git push origin main

# 2. In Vercel Dashboard
# - Import repo
# - Add HF_API_KEY to environment variables
# - Deploy!
```

### Run Tests
```bash
pip install pytest
pytest tests/ -v
```

### Enable Database
See README.md for MongoDB integration steps

---

## Tips for Best Results

✅ **Do:**
- Use clear section headers (Skills, Experience, Education)
- Include relevant technical keywords
- Use action verbs (managed, developed, designed)
- Keep resume to 300-800 words
- List complete contact information

❌ **Don't:**
- Use graphics or unusual formatting
- Include photos or icons
- Use very long paragraphs
- Have gaps without explanation
- Use overly creative fonts

---

## Support

For help:
- Check README.md for full documentation
- Review code comments for implementation details
- Check .env.example for required environment variables

Happy optimizing! 🚀
