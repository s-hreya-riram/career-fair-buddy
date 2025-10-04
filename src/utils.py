"""
Utility functions for Career Fair Buddy
Common helper functions used across the application
"""
import re
import time
import random
from typing import List, Optional, Tuple


def extract_booth_numbers(text: str) -> List[str]:
    """Extract booth numbers from text using regex"""
    booth_matches = re.findall(r'([A-Z]\d{2,3})', text)
    return list(set(booth_matches))


def sort_companies_by_booth(companies: List[dict]) -> List[dict]:
    """Sort companies by booth number (A01, A02, A03, etc.)"""
    def booth_sort_key(company):
        booth = company.get('booth_number', '')
        try:
            letter = booth[0]  # A, B, C, D
            number = int(booth[1:])  # 01, 02, 03, etc.
            return (letter, number)
        except (IndexError, ValueError):
            return (booth, 0)  # Fallback for malformed booth numbers
    
    return sorted(companies, key=booth_sort_key)


def get_booth_page_mapping(booth_number: str, is_day2: bool = False) -> Optional[int]:
    """Get the page number where a specific booth is located"""
    if not booth_number:
        return None
        
    booth_prefix = booth_number[0]
    try:
        booth_num = int(booth_number[1:])
    except (IndexError, ValueError):
        return None
    
    if is_day2:
        # Day 2 booth mappings
        if booth_prefix == 'A':
            return 23 if booth_num <= 22 else 24
        elif booth_prefix == 'B':
            return 26
        elif booth_prefix == 'C':
            return 29
        elif booth_prefix == 'D':
            return 32
    else:
        # Day 1 booth mappings (default)
        if booth_prefix == 'A':
            return 11 if booth_num <= 22 else 12
        elif booth_prefix == 'B':
            return 14
        elif booth_prefix == 'C':
            return 17
        elif booth_prefix == 'D':
            return 20
    
    return None


def exponential_backoff_wait(attempt: int, base_wait: float = 1.0, max_wait: float = 60.0) -> None:
    """Wait with exponential backoff and jitter"""
    wait_time = min(base_wait * (2 ** attempt) + random.uniform(0, 1), max_wait)
    time.sleep(wait_time)


def clean_company_name(raw_name: str) -> str:
    """Clean up extracted company name"""
    if not raw_name:
        return "Unknown Company"
    
    # Remove common patterns
    cleaned = raw_name.strip()
    
    # Remove industry keywords if they appear at the start
    industry_keywords = [
        'Banking & Finance', 'Technology & IT', 'Consulting',
        'Engineering & Manufacturing', 'Energy & Renewables',
        'Public Sector', 'Pharmaceutical, Healthcare, Biomedical Sciences',
        'Chemicals', 'Education', 'Luxury, Retail & Consumer Goods'
    ]
    
    for keyword in industry_keywords:
        if cleaned.startswith(keyword):
            cleaned = cleaned[len(keyword):].strip()
    
    # Clean up extra whitespace
    cleaned = ' '.join(cleaned.split())
    
    return cleaned if cleaned else "Unknown Company"


def is_valid_education_level(level: str) -> bool:
    """Check if education level is valid"""
    from .config import Config
    return level in Config.EDUCATION_LEVELS


def is_valid_industry(industry: str) -> bool:
    """Check if industry is valid"""
    from .config import Config
    return industry in Config.VALID_INDUSTRIES


def get_cache_key(booth_number: str, page_num: int, suffix: str = "") -> str:
    """Generate a consistent cache key"""
    # Use fixed timestamp for deployment compatibility
    base_key = f"{booth_number}_{page_num}_1759480166.4307017"
    return f"{base_key}{suffix}" if suffix else base_key


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def validate_booth_number(booth_number: str) -> bool:
    """Validate booth number format"""
    if not booth_number:
        return False
    
    # Should match pattern like A01, B23, C105, etc.
    pattern = r'^[A-Z]\d{2,3}$'
    return bool(re.match(pattern, booth_number))


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def safe_int_conversion(value: str) -> int:
    """Safely convert string to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def get_venue_from_booth(booth_number: str, is_day2: bool = False) -> str:
    """Get venue name from booth number"""
    if not booth_number:
        return "Unknown"
    
    booth_prefix = booth_number[0]
    day_suffix = " Day 2" if is_day2 else ""
    
    venue_map = {
        'A': f"SRC Hall A{day_suffix}",
        'B': f"SRC Hall B{day_suffix}",
        'C': f"SRC Hall C{day_suffix}",
        'D': f"EA Atrium{day_suffix}"
    }
    
    return venue_map.get(booth_prefix, "Unknown")


def parse_match_percentage(text: str) -> int:
    """Extract match percentage from text"""
    match = re.search(r'(\d+)%', text)
    return int(match.group(1)) if match else 0
