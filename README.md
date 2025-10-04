# 🎯 NUS Career Fair Buddy

A smart, interactive companion app for the NUS Career Fair 2025. Find companies, track your progress, and get AI-powered recommendations tailored to your profile.

## ✨ Features

- **🔍 Smart Search & Filters**: Find companies by name, industry, or education level
- **📱 Mobile-Optimized**: Works seamlessly on phones and desktops
- **✅ Progress Tracking**: Mark companies as visited, interested, or applied
- **🤖 AI Resume Matching**: Upload your resume for personalized company recommendations
- **📊 Interactive Tables**: Sort and filter companies with real-time updates
- **💾 Export Data**: Download your career fair progress as CSV

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/s-hreya-riram/career-fair-buddy.git
   cd career-fair-buddy
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Open in browser**
   Navigate to `http://localhost:8501`

## 📋 Requirements

- Python 3.8+
- Streamlit
- PyMuPDF (for PDF processing)
- Additional dependencies in `requirements.txt`

## 🎪 Career Fair Details

**Event**: NUS Career Fest 2025  
**Dates**: October 8-9, 2025  
**Venues**: Stephen Riady Centre & Engineering Auditorium

## 🏗️ Project Structure

```
career-fair-buddy/
├── streamlit_app.py          # Main application
├── requirements.txt          # Python dependencies
├── data/
│   └── nus-career-fest-2025-student-event-guide-ay2526-sem-1.pdf
└── src/                      # Additional source files
```

## 💡 How to Use

1. **Browse Companies**: Navigate between Day 1 and Day 2 venues
2. **Search & Filter**: Use the search bar and filters to find relevant companies
3. **Track Progress**: Check off companies you've visited or are interested in
4. **Add Notes**: Leave comments about your interactions
5. **AI Matching**: Upload your resume for personalized recommendations
6. **Export Data**: Download your progress for follow-up

## 🔧 Deployment

The app works on any Streamlit-compatible platform:

- **Streamlit Cloud**: Connect your GitHub repo for automatic deployment
- **Heroku**: Use the provided configuration files
- **Local**: Run with `streamlit run streamlit_app.py`
