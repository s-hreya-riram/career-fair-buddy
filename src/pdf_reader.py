"""
PDF Reader for Career Fair documents
Handles PDF processing, text extraction, and company data parsing
"""
import re
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pypdf import PdfReader

from .config import Config
from .cache_manager import CacheManager
from .openai_service import OpenAIService
from .user_manager import UserManager
from .utils import (
    extract_booth_numbers, 
    sort_companies_by_booth, 
    get_booth_page_mapping,
    clean_company_name
)


class CareerFairPDFReader:
    """Main PDF reader class for career fair documents"""
    
    def __init__(self, pdf_path: Optional[str] = None, user_id: Optional[str] = None):
        """Initialize the PDF reader with optional user ID for multi-user support"""
        self.pdf_path = Path(pdf_path) if pdf_path else Config.PDF_FILE_PATH
        self.reader = None
        self.total_pages = 0
        
        # Initialize components
        self.cache_manager = CacheManager()
        self.openai_service = OpenAIService(self.cache_manager)
        self.user_manager = UserManager(user_id)
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        
        self._load_pdf()
    
    def _load_pdf(self):
        """Load the PDF file"""
        try:
            self.reader = PdfReader(str(self.pdf_path))
            self.total_pages = len(self.reader.pages)
            print(f"📄 Loaded PDF with {self.total_pages} pages")
        except Exception as e:
            raise Exception(f"Error loading PDF: {str(e)}")
    
    def get_page_text(self, page_number: int) -> str:
        """Extract text from a specific page (1-indexed)"""
        if page_number < 1 or page_number > self.total_pages:
            raise ValueError(f"Page number must be between 1 and {self.total_pages}")
        
        try:
            page = self.reader.pages[page_number - 1]  # Convert to 0-indexed
            text = page.extract_text()
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from page {page_number}: {str(e)}")
    
    def parse_company_table(self, page_number: int, venue_context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse company information from a specific page"""
        try:
            text = self.get_page_text(page_number)
            lines = [line.strip() for line in text.split('\\n') if line.strip()]
            companies = []
            
            # Extract booth numbers from the page
            booth_numbers = extract_booth_numbers(text)
            booth_numbers = list(set(booth_numbers))
            
            is_day2 = venue_context and "Day 2" in venue_context
            
            # Process each booth
            for booth_number in booth_numbers:
                page_num = get_booth_page_mapping(booth_number, is_day2)
                if not page_num:
                    continue
                
                # Get data using OpenAI service (with caching)
                company_name = self.openai_service.analyze_company_name(
                    booth_number, page_num, str(self.pdf_path), is_day2
                )
                
                industry = self.openai_service.analyze_industry(
                    booth_number, company_name, page_num, str(self.pdf_path), is_day2
                )
                
                education_level = self.openai_service.analyze_education_level(
                    booth_number, page_num, str(self.pdf_path), is_day2
                )
                
                # Get website URL
                website = self.openai_service.analyze_company_website(
                    booth_number, company_name, page_num, is_day2
                )
                
                # Get user interaction data
                user_interaction = self.user_manager.get_interaction(booth_number)
                
                companies.append({
                    'name': company_name,
                    'booth_number': booth_number,
                    'education_level': education_level,
                    'industry': industry,
                    'visited': user_interaction['visited'],
                    'resume_shared': user_interaction['resume_shared'],
                    'apply_online': user_interaction['apply_online'],
                    'interested': user_interaction['interested'],
                    'comments': user_interaction['comments'],
                    'raw_text': f"Booth {booth_number}"
                })
            
            return sort_companies_by_booth(companies)
            
        except Exception as e:
            print(f"Error parsing companies from page {page_number}: {str(e)}")
            return []
    
    def get_venue_companies(self, venue_name: str) -> List[Dict[str, Any]]:
        """Get companies for a specific venue based on page mappings"""
        pages = Config.VENUE_PAGE_MAPPINGS.get(venue_name, [])
        all_companies = []
        
        for page_num in pages:
            try:
                companies = self.parse_company_table(page_num, venue_name)
                all_companies.extend(companies)
            except Exception as e:
                print(f"Warning: Could not parse companies from page {page_num}: {str(e)}")
                continue
        
        return all_companies
    
    def get_cached_venue_companies(self, venue_name: str) -> List[Dict[str, Any]]:
        """Get companies using only cached data (no OpenAI calls)"""
        pages = Config.VENUE_PAGE_MAPPINGS.get(venue_name, [])
        all_companies = []
        
        for page_num in pages:
            try:
                companies = self._parse_company_table_cached_only(page_num, venue_name)
                all_companies.extend(companies)
            except Exception as e:
                print(f"Warning: Could not parse companies from page {page_num}: {str(e)}")
                continue
        
        return all_companies
    
    def _parse_company_table_cached_only(self, page_number: int, venue_context: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse company information using only cached data"""
        try:
            text = self.get_page_text(page_number)
            booth_numbers = extract_booth_numbers(text)
            booth_numbers = list(set(booth_numbers))
            
            companies = []
            is_day2 = venue_context and "Day 2" in venue_context
            
            for booth_number in booth_numbers:
                page_num = get_booth_page_mapping(booth_number, is_day2)
                if not page_num:
                    continue
                
                # Get cached data only
                company_name = self.cache_manager.get_company_name(booth_number, page_num, is_day2) or "Unknown Company"
                industry = self.cache_manager.get_industry(booth_number, page_num, is_day2) or "Unknown"
                education_level = self.cache_manager.get_education_level(booth_number, page_num, is_day2) or "Unknown"
                
                # Get user interaction data
                user_interaction = self.user_manager.get_interaction(booth_number)
                
                companies.append({
                    'name': company_name,
                    'booth_number': booth_number,
                    'education_level': education_level,
                    'industry': industry,
                    'visited': user_interaction['visited'],
                    'resume_shared': user_interaction['resume_shared'],
                    'apply_online': user_interaction['apply_online'],
                    'interested': user_interaction['interested'],
                    'comments': user_interaction['comments'],
                    'raw_text': f"Booth {booth_number}"
                })
            
            return sort_companies_by_booth(companies)
            
        except Exception as e:
            print(f"Error parsing companies from page {page_number}: {str(e)}")
            return []
    
    def update_user_interaction(self, booth_number: str, **kwargs) -> Dict[str, Any]:
        """Update user interaction data for a specific booth"""
        return self.user_manager.update_interaction(booth_number, **kwargs)
    
    def get_user_interaction(self, booth_number: str) -> Dict[str, Any]:
        """Get user interaction data for a specific booth"""
        return self.user_manager.get_interaction(booth_number)
    
    def analyze_resume_match(self, resume_content: str, user_preferences: str = "") -> List[Dict[str, Any]]:
        """Analyze resume and user preferences to find matching companies"""
        if not self.openai_service.is_available():
            print("❌ OpenAI service not available for resume analysis")
            return []
        
        # Get all companies from all venues using cached data
        all_companies = []
        for venue in Config.VENUE_PAGE_MAPPINGS.keys():
            companies = self.get_cached_venue_companies(venue)
            for company in companies:
                company['venue'] = venue
                # Only include companies with meaningful cached data
                if (company['name'] != "Unknown Company" and 
                    company['industry'] != "Unknown" and 
                    company['education_level'] != "Unknown"):
                    all_companies.append(company)
        
        print(f"📊 Analyzing {len(all_companies)} companies for resume match...")
        
        return self.openai_service.analyze_resume_match(resume_content, all_companies, user_preferences)
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text content from uploaded PDF resume"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(pdf_file.read())
                temp_path = temp_file.name
            
            # Extract text using PyPDF
            reader = PdfReader(temp_path)
            text_content = ""
            
            for page in reader.pages:
                text_content += page.extract_text() + "\\n"
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return text_content.strip()
            
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache_manager.get_stats()
    
    def check_cache_completeness(self, venue_name: Optional[str] = None) -> Dict[str, Any]:
        """Check cache completion status"""
        return self.cache_manager.check_completeness(venue_name)
    
    def preload_all_openai_data(self, venue_name: Optional[str] = None) -> Dict[str, Any]:
        """Preload all OpenAI data for complete offline operation"""
        if not self.openai_service.is_available():
            return {'error': 'OpenAI service not available'}
        
        venues = [venue_name] if venue_name else list(Config.VENUE_PAGE_MAPPINGS.keys())
        
        total_stats = {
            'education_cache_hits': 0,
            'education_api_calls': 0,
            'company_cache_hits': 0, 
            'company_api_calls': 0,
            'industry_cache_hits': 0,
            'industry_api_calls': 0,
            'total_booths_processed': 0
        }
        
        for venue in venues:
            print(f"🏢 Processing {venue}...")
            
            pages = Config.VENUE_PAGE_MAPPINGS.get(venue, [])
            booth_numbers = []
            
            # Extract all booth numbers from pages
            for page_num in pages:
                try:
                    text = self.get_page_text(page_num)
                    booth_matches = extract_booth_numbers(text)
                    booth_numbers.extend(booth_matches)
                except Exception as e:
                    print(f"⚠️ Warning: Could not extract booths from page {page_num}: {e}")
            
            # Remove duplicates and sort
            booth_numbers = sorted(list(set(booth_numbers)))
            print(f"📍 Found {len(booth_numbers)} booths: {booth_numbers[:5]}{'...' if len(booth_numbers) > 5 else ''}")
            
            is_day2 = "Day 2" in venue
            
            # Process each booth for all three data types
            for booth_number in booth_numbers:
                page_num = get_booth_page_mapping(booth_number, is_day2)
                if not page_num:
                    continue
                
                print(f"🔄 Processing {booth_number}...", end=" ")
                
                # 1. Education Level
                if self.cache_manager.get_education_level(booth_number, page_num, is_day2):
                    total_stats['education_cache_hits'] += 1
                    print("📚✓", end=" ")
                else:
                    education_level = self.openai_service.analyze_education_level(
                        booth_number, page_num, str(self.pdf_path), is_day2
                    )
                    total_stats['education_api_calls'] += 1
                    print(f"📚{education_level[:1] if education_level != 'Unknown' else '❌'}", end=" ")
                
                # 2. Company Name
                if self.cache_manager.get_company_name(booth_number, page_num, is_day2):
                    total_stats['company_cache_hits'] += 1
                    print("🏢✓", end=" ")
                else:
                    company_name = self.openai_service.analyze_company_name(
                        booth_number, page_num, str(self.pdf_path), is_day2
                    )
                    total_stats['company_api_calls'] += 1
                    print("🏢✓" if company_name != "Unknown" else "🏢❌", end=" ")
                
                # 3. Industry
                if self.cache_manager.get_industry(booth_number, page_num, is_day2):
                    total_stats['industry_cache_hits'] += 1
                    print("🏭✓")
                else:
                    # Get the cached company name for industry analysis
                    cached_company = self.cache_manager.get_company_name(booth_number, page_num, is_day2) or "Unknown Company"
                    industry = self.openai_service.analyze_industry(
                        booth_number, cached_company, page_num, str(self.pdf_path), is_day2
                    )
                    total_stats['industry_api_calls'] += 1
                    print("🏭✓" if industry != "Unknown" else "🏭❌")
                
                total_stats['total_booths_processed'] += 1
                
                # Save cache every 10 booths
                if total_stats['total_booths_processed'] % 10 == 0:
                    self.cache_manager.save_cache()
        
        # Final save
        self.cache_manager.save_cache()
        
        return total_stats
    
    def clear_cache(self):
        """Clear the OpenAI vision cache"""
        self.cache_manager.clear()
    
    def get_user_summary(self) -> Dict[str, Any]:
        """Get user interaction summary"""
        return self.user_manager.get_user_summary()
    
    def export_user_data(self) -> str:
        """Export user data to CSV format"""
        return self.user_manager.export_to_csv()
    
    @property
    def user_id(self) -> str:
        """Get current user ID"""
        return self.user_manager.user_id
