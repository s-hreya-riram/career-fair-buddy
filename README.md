# 🎯 NUS Career Fair Buddy

Career Fair Buddy is an AI-powered web application designed to help students navigate the **NUS Career Fair 2025** (October 8-9, 2025). The app provides intelligent company matching, venue maps, and interaction tracking to maximize your career fair experience.

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

## 🏗️ Project Structure

```
career-fair-buddy/
├── main.py                  # Main Streamlit application (NEW - modular version)
├── app.py                   # Legacy monolithic version (deprecated)
├── streamlit_app.py         # Legacy UI file (deprecated)
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── .gitignore              # Git ignore rules
├── .streamlit/             # Streamlit configuration
│   └── secrets.toml        # API keys (not in git)
├── data/                   # PDF and data files
│   └── nus-career-fest-2025-student-event-guide-ay2526-sem-1.pdf
└── src/                    # NEW: Modular source code
    ├── __init__.py         # Package initialization
    ├── config.py           # Configuration and settings
    ├── utils.py            # Utility functions
    ├── cache_manager.py    # OpenAI cache management
    ├── user_manager.py     # Multi-user data management
    ├── openai_service.py   # OpenAI API integration
    ├── pdf_reader.py       # PDF processing and company extraction
    └── ui/                 # UI components
        ├── __init__.py     # UI package init
        ├── styles.py       # CSS styles and theming
        └── mobile.py       # Mobile device adaptations
```

### 🔄 Migration from Legacy Version

The codebase has been refactored into a **modular architecture** for better:
- **Maintainability**: Separated concerns into focused modules
- **Reusability**: Components can be used independently
- **Testing**: Each module can be tested in isolation
- **Scalability**: Easy to extend and modify individual features

**To use the new modular version:**
```bash
streamlit run main.py
```

**Legacy version (deprecated):**
```bash
streamlit run streamlit_app.py  # Still works but deprecated
```

## � Architecture Benefits

### **Modular Design Advantages**

| Aspect | Legacy Version | New Modular Version |
|--------|---------------|-------------------|
| **Code Organization** | Single 2000+ line file | 8 focused modules ~200-400 lines each |
| **Maintainability** | Hard to modify | Easy to update individual components |
| **Testing** | Monolithic testing | Unit tests per module |
| **Reusability** | Copy entire codebase | Import specific components |
| **Team Development** | Merge conflicts | Parallel development on different modules |
| **Debugging** | Search entire file | Target specific module |

### **Component Responsibilities**

- **`config.py`**: Centralized settings, API keys, venue mappings
- **`pdf_reader.py`**: PDF processing orchestration and main API
- **`openai_service.py`**: AI analysis with retry logic and caching
- **`cache_manager.py`**: Intelligent caching system for performance
- **`user_manager.py`**: Multi-user data isolation and metrics
- **`utils.py`**: Common helper functions and data processing
- **`ui/`**: Responsive UI components and mobile optimization

### **For Developers**

```python
# Easy to import specific functionality
from src.pdf_reader import CareerFairPDFReader
from src.openai_service import OpenAIService
from src.user_manager import UserManager

# Initialize with custom configuration
reader = CareerFairPDFReader(user_id="custom_user")
companies = reader.get_venue_companies("SRC Hall A")
```

### **Future Extensions**

The modular architecture makes it easy to:
- Add new AI providers (Claude, Gemini) alongside OpenAI
- Implement different caching strategies (Redis, database)
- Create new UI frameworks (Gradio, Flask) using the same core
- Add analytics and monitoring modules
- Integrate with external APIs (job boards, company databases)

## �🔧 Deployment

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

## 📈 Scaling & Architecture

### Design Philosophy
This application is specifically designed for **short-duration events** (1-3 days) with a focus on:
- **Low maintenance overhead**: No database setup or management required
- **Cost optimization**: Minimal infrastructure requirements
- **Quick deployment**: Works out-of-the-box on free hosting tiers

### Multi-User System
- **User Isolation**: Each user gets a unique 8-character UUID for data separation
- **Server-side Storage**: User interactions stored as individual JSON files
- **Cross-device Sync**: UUIDs persist in browser localStorage for seamless access

### Scaling Limitations
Our file-based approach has **intentional limitations** suitable for career fair events:

| Metric | Capacity | Warning Threshold |
|--------|----------|-------------------|
| **Concurrent Users** | ~25,000 | 20,000 users |
| **Storage Usage** | ~1GB (Streamlit limit) | 400MB |
| **Performance** | Optimal < 5,000 users | Degrades > 10,000 |

### Performance Monitoring
The app includes built-in metrics in the sidebar:
- Active user count (24-hour window)
- Storage usage tracking
- Performance warnings at scale

### Why Not a Database?
For a **2-day career fair event**, we prioritized:
1. **Zero maintenance**: No database backups, migrations, or downtime
2. **Cost efficiency**: Runs entirely on free Streamlit Cloud tier
3. **Simplicity**: Single repository deployment with no external dependencies
4. **Event duration**: File cleanup happens automatically after the event

### Scaling Beyond File Storage
If you need to support larger events (>25k users) or longer durations:

1. **Database Migration**: 
   - Replace JSON files with PostgreSQL/MongoDB
   - Add connection pooling and caching layers
   - Implement proper user authentication

2. **Infrastructure Upgrade**:
   - Move to containerized deployment (Docker + K8s)
   - Add Redis for session management
   - Implement horizontal scaling

3. **Performance Optimization**:
   - Add CDN for static assets
   - Implement database indexing
   - Add API rate limiting

### Event-Specific Optimization
Current architecture is **perfect for career fairs** because:
- Users interact intensively for 1-2 days
- No long-term data retention needed
- High read-to-write ratio (browsing vs. bookmarking)
- Predictable usage patterns during event hours
