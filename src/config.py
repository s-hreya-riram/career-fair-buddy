"""
Configuration settings for Career Fair Buddy
Centralizes all configuration and environment variables
"""
import os
from pathlib import Path


class Config:
    """Main configuration class"""
    
    # File paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    CACHE_DIR = PROJECT_ROOT
    
    # PDF file path
    PDF_FILE_PATH = DATA_DIR / "nus-career-fest-2025-student-event-guide-ay2526-sem-1.pdf"
    
    # Cache files
    OPENAI_CACHE_FILE = "openai_vision_cache.json"
    USER_DATA_PREFIX = "user_interactions_"
    
    # OpenAI configuration
    OPENAI_API_KEY = None
    OPENAI_MODEL = "gpt-4o"
    OPENAI_MODEL_MINI = "gpt-4o-mini"
    OPENAI_MAX_RETRIES = 5
    OPENAI_TIMEOUT = 20
    
    # System limits and thresholds
    MAX_USERS_WARNING = 20000
    MAX_STORAGE_WARNING_MB = 400
    ACTIVITY_WINDOW_HOURS = 24
    
    # Venue mappings organized by day
    VENUE_PAGE_MAPPINGS = {
        # Day 1 venues
        'SRC Hall A': [11, 12],
        'SRC Hall B': [14, 15], 
        'SRC Hall C': [17, 18],
        'EA Atrium': [20, 21],
        # Day 2 venues
        'SRC Hall A Day 2': [23, 24],
        'SRC Hall B Day 2': [26, 27],
        'SRC Hall C Day 2': [29, 30],
        'EA Atrium Day 2': [32, 33, 34]
    }
    
    # Day-based organization for easier navigation
    DAY_VENUES = {
        'Day 1': {
            'SRC Hall A': [11, 12],
            'SRC Hall B': [14, 15], 
            'SRC Hall C': [17, 18],
            'EA Atrium': [20, 21]
        },
        'Day 2': {
            'SRC Hall A': [23, 24],
            'SRC Hall B': [26, 27],
            'SRC Hall C': [29, 30],
            'EA Atrium': [32, 33, 34]
        }
    }
    
    # All venues list for backward compatibility
    ALL_VENUES = list(VENUE_PAGE_MAPPINGS.keys())
    
    # Industry categories
    VALID_INDUSTRIES = [
        'Banking & Finance', 'Technology & IT', 'Consulting',
        'Engineering & Manufacturing', 'Energy & Renewables',
        'Public Sector', 'Pharmaceutical, Healthcare, Biomedical Sciences',
        'Chemicals', 'Education', 'Luxury, Retail & Consumer Goods',
        'Real Estate & Construction', 'Financial Services', 'Banks (Local/Asia)',
        'Transport, Maritime', 'Healthcare'
    ]
    
    # Education levels
    EDUCATION_LEVELS = ["Undergraduate", "Postgraduate", "Both"]
    
    @classmethod
    def setup_openai_key(cls):
        """Set up OpenAI API key from various sources"""
        try:
            import streamlit as st
            # Try Streamlit secrets first (for deployment)
            try:
                cls.OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
                print("🔑 Using Streamlit secrets for API key")
                return True
            except:
                pass
        except ImportError:
            pass
        
        # Try environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            cls.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
            if cls.OPENAI_API_KEY:
                print("🔑 Using .env file for API key")
                return True
        except ImportError:
            pass
        
        # Fallback to direct environment variable
        cls.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        if cls.OPENAI_API_KEY:
            print("🔑 Using environment variable for API key")
            return True
        
        print("❌ No OpenAI API key found")
        return False
    
    @classmethod
    def validate_setup(cls):
        """Validate the configuration setup"""
        issues = []
        
        if not cls.PDF_FILE_PATH.exists():
            issues.append(f"PDF file not found: {cls.PDF_FILE_PATH}")
        
        if not cls.OPENAI_API_KEY:
            issues.append("OpenAI API key not configured")
        
        if not cls.DATA_DIR.exists():
            issues.append(f"Data directory not found: {cls.DATA_DIR}")
        
        return issues
    
    @classmethod
    def get_venues_for_day(cls, day: str) -> dict:
        """Get venues for a specific day"""
        return cls.DAY_VENUES.get(day, {})
    
    @classmethod
    def get_day_from_venue(cls, venue_name: str) -> str:
        """Get day from venue name"""
        if "Day 2" in venue_name:
            return "Day 2"
        return "Day 1"
    
    @classmethod
    def get_clean_venue_name(cls, venue_name: str) -> str:
        """Get clean venue name without day suffix"""
        return venue_name.replace(" Day 2", "")
    
    @classmethod
    def get_full_venue_name(cls, clean_name: str, day: str) -> str:
        """Get full venue name with day suffix"""
        if day == "Day 2":
            return f"{clean_name} Day 2"
        return clean_name


# Initialize configuration
Config.setup_openai_key()
