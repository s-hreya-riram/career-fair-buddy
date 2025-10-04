"""
Cache management for OpenAI API responses
Handles caching, loading, and saving of vision analysis results
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .config import Config
from .utils import get_cache_key, format_file_size


class CacheManager:
    """Manages OpenAI vision cache for faster loading and reduced API calls"""
    
    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or Path(Config.OPENAI_CACHE_FILE)
        self.cache: Dict[str, Any] = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache file: {e}")
        return {}
    
    def save_cache(self) -> bool:
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            return True
        except Exception as e:
            print(f"Error: Could not save cache file: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        self.cache[key] = value
    
    def has(self, key: str) -> bool:
        """Check if key exists in cache"""
        return key in self.cache
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
    
    def get_education_key(self, booth_number: str, page_num: int, is_day2: bool = False) -> str:
        """Get cache key for education level"""
        suffix = "_day2" if is_day2 else ""
        return get_cache_key(booth_number, page_num, suffix)
    
    def get_company_key(self, booth_number: str, page_num: int, is_day2: bool = False) -> str:
        """Get cache key for company name"""
        suffix = "_day2" if is_day2 else ""
        return f"company_{get_cache_key(booth_number, page_num, suffix)}"
    
    def get_industry_key(self, booth_number: str, page_num: int, is_day2: bool = False) -> str:
        """Get cache key for industry"""
        suffix = "_day2" if is_day2 else ""
        return f"industry_{get_cache_key(booth_number, page_num, suffix)}"
    
    def get_education_level(self, booth_number: str, page_num: int, is_day2: bool = False) -> Optional[str]:
        """Get cached education level"""
        key = self.get_education_key(booth_number, page_num, is_day2)
        return self.get(key)
    
    def set_education_level(self, booth_number: str, page_num: int, level: str, is_day2: bool = False) -> None:
        """Cache education level"""
        key = self.get_education_key(booth_number, page_num, is_day2)
        self.set(key, level)
    
    def get_company_name(self, booth_number: str, page_num: int, is_day2: bool = False) -> Optional[str]:
        """Get cached company name"""
        key = self.get_company_key(booth_number, page_num, is_day2)
        return self.get(key)
    
    def set_company_name(self, booth_number: str, page_num: int, name: str, is_day2: bool = False) -> None:
        """Cache company name"""
        key = self.get_company_key(booth_number, page_num, is_day2)
        self.set(key, name)
    
    def get_industry(self, booth_number: str, page_num: int, is_day2: bool = False) -> Optional[str]:
        """Get cached industry"""
        key = self.get_industry_key(booth_number, page_num, is_day2)
        return self.get(key)
    
    def set_industry(self, booth_number: str, page_num: int, industry: str, is_day2: bool = False) -> None:
        """Cache industry"""
        key = self.get_industry_key(booth_number, page_num, is_day2)
        self.set(key, industry)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        education_entries = 0
        company_entries = 0
        industry_entries = 0
        other_entries = 0
        
        for key in self.cache.keys():
            if key.startswith('industry_'):
                industry_entries += 1
            elif key.startswith('company_'):
                company_entries += 1
            elif '_' in key and not key.startswith(('industry_', 'company_')):
                education_entries += 1
            else:
                other_entries += 1
        
        file_size = 0
        if self.cache_file.exists():
            file_size = self.cache_file.stat().st_size
        
        return {
            'total_entries': len(self.cache),
            'education_entries': education_entries,
            'company_entries': company_entries,
            'industry_entries': industry_entries,
            'other_entries': other_entries,
            'file_exists': self.cache_file.exists(),
            'file_path': str(self.cache_file),
            'file_size_bytes': file_size,
            'file_size_formatted': format_file_size(file_size)
        }
    
    def check_completeness(self, venue_name: Optional[str] = None) -> Dict[str, Any]:
        """Check cache completeness for venues"""
        from .utils import extract_booth_numbers, get_booth_page_mapping
        
        if venue_name:
            venues = [venue_name]
        else:
            venues = list(Config.VENUE_PAGE_MAPPINGS.keys())
        
        total_booths = 0
        cached_education = 0
        cached_companies = 0
        cached_industries = 0
        
        for venue in venues:
            pages = Config.VENUE_PAGE_MAPPINGS.get(venue, [])
            booth_numbers = []
            
            # This would need access to PDF reader - simplified for now
            # In practice, this would extract booth numbers from each page
            # For now, estimate based on venue patterns
            if 'A' in venue:
                booth_numbers = [f"A{i:02d}" for i in range(1, 39)]
            elif 'B' in venue:
                booth_numbers = [f"B{i:02d}" for i in range(1, 25)]
            elif 'C' in venue:
                booth_numbers = [f"C{i:02d}" for i in range(1, 20)]
            elif 'D' in venue:
                booth_numbers = [f"D{i:02d}" for i in range(1, 15)]
            
            is_day2 = "Day 2" in venue
            total_booths += len(booth_numbers)
            
            for booth_number in booth_numbers:
                page_num = get_booth_page_mapping(booth_number, is_day2)
                if not page_num:
                    continue
                
                # Check cache status
                if self.get_education_level(booth_number, page_num, is_day2):
                    cached_education += 1
                if self.get_company_name(booth_number, page_num, is_day2):
                    cached_companies += 1
                if self.get_industry(booth_number, page_num, is_day2):
                    cached_industries += 1
        
        if total_booths == 0:
            return {
                'total_booths': 0,
                'education_cached_pct': 0,
                'company_cached_pct': 0,
                'industry_cached_pct': 0,
                'fully_cached_pct': 0
            }
        
        education_pct = round((cached_education / total_booths) * 100, 1)
        company_pct = round((cached_companies / total_booths) * 100, 1)
        industry_pct = round((cached_industries / total_booths) * 100, 1)
        
        fully_cached = min(cached_education, cached_companies, cached_industries)
        fully_cached_pct = round((fully_cached / total_booths) * 100, 1)
        
        return {
            'total_booths': total_booths,
            'education_cached': cached_education,
            'education_cached_pct': education_pct,
            'company_cached': cached_companies,
            'company_cached_pct': company_pct,
            'industry_cached': cached_industries,
            'industry_cached_pct': industry_pct,
            'fully_cached': fully_cached,
            'fully_cached_pct': fully_cached_pct,
            'ready_for_offline': fully_cached_pct == 100.0
        }
