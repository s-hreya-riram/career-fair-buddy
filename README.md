# 🎯 NUS Career Fair Buddy

A smart, interactive companion app for the NUS Career Fair 2025. Find companies, track your progress, and get AI-powered recommendations tailored to your profile.

## ✨ Features

- **🔍 Smart Search & Filters**: Find companies by name, industry, or education level
- **📱 Mobile-Optimized**: Works seamlessly on phones and desktops
- **✅ Progress Tracking**: Mark companies as visited, interested, or applied
- **🤖 AI Resume Matching**: Upload your resume for personalized company recommendations
- **📊 Interactive Tables**: Sort and filter companies with real-time updates
- **💾 Export Data**: Download your career fair progress as CSV

## 🎪 Career Fair Details

**Event**: NUS Career Fest 2025  
**Dates**: October 8-9, 2025  
**Venues**: Stephen Riady Centre & Engineering Auditorium


## 💡 How to Use

1. **Browse Companies**: Navigate between Day 1 and Day 2 venues
2. **Search & Filter**: Use the search bar and filters to find relevant companies
3. **Track Progress**: Check off companies you've visited or are interested in
4. **Add Notes**: Leave comments about your interactions
5. **AI Matching**: Upload your resume for personalized recommendations
6. **Export Data**: Download your progress for follow-up


## 📋 Requirements

- Python 3.8+
- Streamlit
- PyMuPDF (for PDF processing)
- Additional dependencies in `requirements.txt`

## 🏗️ Project Structure

```
career-fair-buddy/
├── streamlit_app.py          # Main application
├── requirements.txt          # Python dependencies
├── data/
│   └── nus-career-fest-2025-student-event-guide-ay2526-sem-1.pdf
└── src/                      # Additional source files
```

## 🔧 Deployment

### Streamlit Cloud (Recommended)
1. Fork or clone this repository
2. Connect your GitHub account to [Streamlit Cloud](https://share.streamlit.io/)
3. Deploy directly from your GitHub repository

### Local Development
1. Clone the repository and navigate to the project directory

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source ./venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory for local testing and a `secrets.toml` file under .streamlit for connecting to OpenAI through the Streamlit app:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. Run the application:
   ```
   streamlit run src/app.py
   ```

The app will open in your browser.

### 
