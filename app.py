import os
import time
import base64
import io
import json
import re
from pathlib import Path
from pypdf import PdfReader
from PIL import Image

# Load environment variables and OpenAI
try:
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
except ImportError:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
OPENAI_AVAILABLE = False
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        OPENAI_AVAILABLE = True
    except ImportError:
        openai_client = None
else:
    openai_client = None

class CareerFairPDFReader:
    def __init__(self, pdf_path):
        """Initialize the PDF reader with the path to the career fair PDF"""
        self.pdf_path = Path(pdf_path)
        self.reader = None
        self.total_pages = 0
        
        # Initialize OpenAI vision cache
        self.cache_file = Path("openai_vision_cache.json")
        self.vision_cache = self._load_cache()
        
        # Initialize user data for tracking booth interactions
        self.user_data_file = Path("user_interactions.json")
        self.user_data = self._load_user_data()
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self._load_pdf()
    
    def _load_cache(self):
        """Load the OpenAI vision analysis cache from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_cache(self):
        """Save the OpenAI vision analysis cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.vision_cache, f, indent=2)
        except Exception:
            pass
    
    def _load_user_data(self):
        """Load user interaction data from file"""
        try:
            if self.user_data_file.exists():
                with open(self.user_data_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_user_data(self):
        """Save user interaction data to file"""
        try:
            with open(self.user_data_file, 'w') as f:
                json.dump(self.user_data, f, indent=2)
        except Exception:
            pass
    
    def _get_cache_key(self, booth_number, page_num):
        """Generate a cache key for OpenAI vision analysis"""
        # Include PDF modification time to invalidate cache if PDF changes
        try:
            pdf_mtime = os.path.getmtime(self.pdf_path)
            return f"{booth_number}_{page_num}_{pdf_mtime}"
        except:
            return f"{booth_number}_{page_num}"
    
    def get_cache_stats(self):
        """Get comprehensive statistics about the OpenAI vision cache"""
        
        # Count different cache types
        education_entries = 0
        company_entries = 0
        industry_entries = 0
        other_entries = 0
        
        for key in self.vision_cache.keys():
            if key.startswith('industry_'):
                industry_entries += 1
            elif key.startswith('company_'):
                company_entries += 1
            elif '_' in key and not key.startswith(('industry_', 'company_')):
                education_entries += 1
            else:
                other_entries += 1
        
        return {
            'total_entries': len(self.vision_cache),
            'education_entries': education_entries,
            'company_entries': company_entries, 
            'industry_entries': industry_entries,
            'other_entries': other_entries,
            'cache_file_exists': self.cache_file.exists(),
            'cache_file_path': str(self.cache_file),
            'cache_file_size_mb': round(self.cache_file.stat().st_size / 1024 / 1024, 2) if self.cache_file.exists() else 0
        }
    
    def clear_cache(self):
        """Clear the OpenAI vision cache"""
        self.vision_cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
    
    def update_user_interaction(self, booth_number, visited=None, resume_shared=None, apply_online=None, interested=None, comments=None):
        """Update user interaction data for a specific booth"""
        if booth_number not in self.user_data:
            self.user_data[booth_number] = {
                'visited': False,
                'resume_shared': False,
                'apply_online': False,
                'interested': False,
                'comments': ''
            }
        
        # Update only the provided fields
        if visited is not None:
            self.user_data[booth_number]['visited'] = visited
        if resume_shared is not None:
            self.user_data[booth_number]['resume_shared'] = resume_shared
        if apply_online is not None:
            self.user_data[booth_number]['apply_online'] = apply_online
        if interested is not None:
            self.user_data[booth_number]['interested'] = interested
        if comments is not None:
            self.user_data[booth_number]['comments'] = comments
        
        self._save_user_data()
        return self.user_data[booth_number]
    
    def get_user_interaction(self, booth_number):
        """Get user interaction data for a specific booth"""
        data = self.user_data.get(booth_number, {})
        # Ensure all fields are present with defaults
        return {
            'visited': data.get('visited', False),
            'resume_shared': data.get('resume_shared', False),
            'apply_online': data.get('apply_online', False),
            'interested': data.get('interested', False),
            'comments': data.get('comments', '')
        }
    
    def get_user_stats(self):
        """Get summary statistics of user interactions"""
        total_booths = len(self.user_data)
        visited_count = sum(1 for data in self.user_data.values() if data.get('visited', False))
        resume_shared_count = sum(1 for data in self.user_data.values() if data.get('resume_shared', False))
        apply_online_count = sum(1 for data in self.user_data.values() if data.get('apply_online', False))
        interested_count = sum(1 for data in self.user_data.values() if data.get('interested', False))
        with_comments_count = sum(1 for data in self.user_data.values() if data.get('comments', '').strip())
        
        return {
            'total_tracked_booths': total_booths,
            'visited_booths': visited_count,
            'resumes_shared': resume_shared_count,
            'need_online_applications': apply_online_count,
            'interested_booths': interested_count,
            'booths_with_comments': with_comments_count
        }
    
    def clear_user_data(self):
        """Clear all user interaction data"""
        self.user_data = {}
        if self.user_data_file.exists():
            self.user_data_file.unlink()
    
    def export_user_data(self, venue_name=None):
        """Export user interaction data with company details"""
        if venue_name:
            venues = [venue_name]
        else:
            venues = ['SRC Hall A', 'SRC Hall B', 'SRC Hall C', 'EA Atrium',
                     'SRC Hall A Day 2', 'SRC Hall B Day 2', 'SRC Hall C Day 2', 'EA Atrium Day 2']
        
        export_data = []
        
        for venue in venues:
            companies = self.get_venue_companies(venue)
            for company in companies:
                booth_number = company['booth_number']
                user_interaction = self.get_user_interaction(booth_number)
                
                export_data.append({
                    'venue': venue,
                    'booth_number': booth_number,
                    'company_name': company['name'],
                    'industry': company['industry'],
                    'education_level': company['education_level'],
                    'visited': user_interaction['visited'],
                    'resume_shared': user_interaction['resume_shared'],
                    'apply_online': user_interaction['apply_online'],
                    'interested': user_interaction['interested'],
                    'comments': user_interaction['comments']
                })
        
        return export_data
    
    def mark_visited(self, booth_number, visited=True):
        """Quick method to mark a booth as visited"""
        return self.update_user_interaction(booth_number, visited=visited)
    
    def mark_resume_shared(self, booth_number, shared=True):
        """Quick method to mark resume as shared"""
        return self.update_user_interaction(booth_number, resume_shared=shared)
    
    def mark_apply_online(self, booth_number, apply=True):
        """Quick method to mark for online application"""
        return self.update_user_interaction(booth_number, apply_online=apply)
    
    def mark_interested(self, booth_number, interested=True):
        """Quick method to mark a booth as interested"""
        return self.update_user_interaction(booth_number, interested=interested)
    
    def add_comment(self, booth_number, comment):
        """Quick method to add/update comment"""
        return self.update_user_interaction(booth_number, comments=comment)

    def check_cache_completeness(self, venue_name=None):
        """Check what percentage of booth data is cached vs needs OpenAI calls"""
        
        if venue_name:
            venues = [venue_name]
        else:
            venues = ['SRC Hall A', 'SRC Hall B', 'SRC Hall C', 'EA Atrium',
                     'SRC Hall A Day 2', 'SRC Hall B Day 2', 'SRC Hall C Day 2', 'EA Atrium Day 2']
        
        total_booths = 0
        cached_education = 0
        cached_companies = 0
        cached_industries = 0
        
        for venue in venues:
            venue_page_mappings = {
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
            
            pages = venue_page_mappings.get(venue, [])
            booth_numbers = []
            
            for page_num in pages:
                try:
                    text = self.get_page_text(page_num)
                    import re
                    booth_matches = re.findall(r'([A-Z]\d{2,3})', text)
                    booth_numbers.extend(booth_matches)
                except Exception:
                    continue
            
            booth_numbers = list(set(booth_numbers))
            total_booths += len(booth_numbers)
            
            for booth_number in booth_numbers:
                page_num = self._find_booth_page(booth_number)
                if not page_num:
                    continue
                
                # Check education cache
                education_key = self._get_cache_key(booth_number, page_num)
                if education_key in self.vision_cache:
                    cached_education += 1
                
                # Check company cache
                company_key = f"company_{booth_number}_{page_num}_{os.path.getmtime(self.pdf_path) if self.pdf_path.exists() else 0}"
                if company_key in self.vision_cache:
                    cached_companies += 1
                
                # Check industry cache
                industry_key = f"industry_{booth_number}_{page_num}_{os.path.getmtime(self.pdf_path) if self.pdf_path.exists() else 0}"
                if industry_key in self.vision_cache:
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
        
        # Fully cached means all three data types are cached
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
    
    def preload_cache_for_venue(self, venue_name):
        """Preload cache for all booths in a venue to batch process OpenAI calls"""
        companies = self.get_venue_companies(venue_name)
        
        cache_hits = 0
        api_calls = 0
        
        for company in companies:
            booth_number = company.get('booth_number')
            if booth_number:
                page_num = self._find_booth_page(booth_number)
                if page_num:
                    cache_key = self._get_cache_key(booth_number, page_num)
                    
                    if cache_key in self.vision_cache:
                        cache_hits += 1
                    else:
                        # This will trigger the OpenAI call and cache the result
                        education_level = self._analyze_with_openai_vision(booth_number, page_num)
                        if education_level:
                            self.vision_cache[cache_key] = education_level
                            api_calls += 1
        
        if api_calls > 0:
            self._save_cache()
        
        return {'cache_hits': cache_hits, 'api_calls': api_calls}

    def preload_all_openai_data(self, venue_name=None):
        """Preload ALL OpenAI data (company names, industries, education levels) for complete offline operation"""
        
        if venue_name:
            venues = [venue_name]
        else:
            venues = ['SRC Hall A', 'SRC Hall B', 'SRC Hall C', 'EA Atrium',
                     'SRC Hall A Day 2', 'SRC Hall B Day 2', 'SRC Hall C Day 2', 'EA Atrium Day 2']
        
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
            print(f"\n🏢 Processing {venue}...")
            
            # Get all booth numbers for this venue
            venue_page_mappings = {
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
            
            pages = venue_page_mappings.get(venue, [])
            booth_numbers = []
            
            # Extract all booth numbers from pages
            for page_num in pages:
                try:
                    text = self.get_page_text(page_num)
                    import re
                    booth_matches = re.findall(r'([A-Z]\d{2,3})', text)
                    booth_numbers.extend(booth_matches)
                except Exception as e:
                    print(f"  ⚠️  Warning: Could not extract booths from page {page_num}: {e}")
            
            # Remove duplicates and sort
            booth_numbers = sorted(list(set(booth_numbers)))
            print(f"  📍 Found {len(booth_numbers)} booths: {booth_numbers[:5]}{'...' if len(booth_numbers) > 5 else ''}")
            
            # Process each booth for all three data types
            for booth_number in booth_numbers:
                page_num = self._find_booth_page(booth_number)
                if not page_num:
                    continue
                
                print(f"  🔄 Processing {booth_number}...", end=" ")
                
                # 1. Education Level Cache
                education_cache_key = self._get_cache_key(booth_number, page_num)
                if education_cache_key in self.vision_cache:
                    total_stats['education_cache_hits'] += 1
                    print("📚✓", end=" ")
                else:
                    education_level = self._analyze_with_openai_vision(booth_number, page_num)
                    if education_level:
                        self.vision_cache[education_cache_key] = education_level
                        total_stats['education_api_calls'] += 1
                        print(f"📚{education_level[:1]}", end=" ")
                    else:
                        print("📚❌", end=" ")
                
                # 2. Company Name Cache
                company_cache_key = f"company_{booth_number}_{page_num}_{os.path.getmtime(self.pdf_path) if self.pdf_path.exists() else 0}"
                if company_cache_key in self.vision_cache:
                    total_stats['company_cache_hits'] += 1
                    print("🏢✓", end=" ")
                else:
                    company_name = self._analyze_company_name_with_openai_vision(booth_number, page_num)
                    if company_name and company_name != "Unknown":
                        self.vision_cache[company_cache_key] = company_name
                        total_stats['company_api_calls'] += 1
                        print(f"🏢✓", end=" ")
                    else:
                        self.vision_cache[company_cache_key] = "Unknown"
                        total_stats['company_api_calls'] += 1
                        print("🏢❌", end=" ")
                
                # 3. Industry Cache  
                industry_cache_key = f"industry_{booth_number}_{page_num}_{os.path.getmtime(self.pdf_path) if self.pdf_path.exists() else 0}"
                if industry_cache_key in self.vision_cache:
                    total_stats['industry_cache_hits'] += 1
                    print("🏭✓")
                else:
                    # Use the company name we just extracted
                    cached_company = self.vision_cache.get(company_cache_key, "Unknown Company")
                    industry = self._analyze_industry_with_openai_vision(booth_number, cached_company, page_num)
                    if industry and industry != "Unknown":
                        self.vision_cache[industry_cache_key] = industry
                        total_stats['industry_api_calls'] += 1
                        print("🏭✓")
                    else:
                        self.vision_cache[industry_cache_key] = "Unknown"
                        total_stats['industry_api_calls'] += 1
                        print("🏭❌")
                
                total_stats['total_booths_processed'] += 1
                
                # Save cache every 10 booths to prevent data loss
                if total_stats['total_booths_processed'] % 10 == 0:
                    self._save_cache()
        
        # Final save
        self._save_cache()
        
        # Print summary
        total_api_calls = (total_stats['education_api_calls'] + 
                          total_stats['company_api_calls'] + 
                          total_stats['industry_api_calls'])
        total_cache_hits = (total_stats['education_cache_hits'] + 
                           total_stats['company_cache_hits'] + 
                           total_stats['industry_cache_hits'])
        
        print(f"\n✅ Preload Complete!")
        print(f"📊 Summary:")
        print(f"   • Booths processed: {total_stats['total_booths_processed']}")
        print(f"   • Total API calls: {total_api_calls}")
        print(f"   • Total cache hits: {total_cache_hits}")
        print(f"   • Education API calls: {total_stats['education_api_calls']}")
        print(f"   • Company API calls: {total_stats['company_api_calls']}")
        print(f"   • Industry API calls: {total_stats['industry_api_calls']}")
        print(f"   • Cache file: {self.cache_file}")
        print(f"   • Cache entries: {len(self.vision_cache)}")
        
        return total_stats
    
    def retry_unknown_industries(self, venue_name):
        """Retry OpenAI analysis for companies that currently have 'Unknown' industry"""
        companies = self.get_venue_companies(venue_name)
        
        retried = 0
        improved = 0
        
        for company in companies:
            if company['industry'] == 'Unknown':
                booth_number = company.get('booth_number')
                company_name = company.get('name')
                
                if booth_number and company_name:
                    # Force a new analysis by removing from cache
                    page_num = self._find_booth_page(booth_number)
                    if page_num:
                        cache_key = f"industry_{booth_number}_{page_num}_{os.path.getmtime(self.pdf_path) if self.pdf_path.exists() else 0}"
                        if cache_key in self.vision_cache:
                            del self.vision_cache[cache_key]
                        
                        # Get new result
                        new_industry = self.determine_industry_with_openai(booth_number, company_name)
                        retried += 1
                        
                        if new_industry != "Unknown":
                            improved += 1
                            print(f"✅ {booth_number}: {company_name[:30]} -> {new_industry}")
                        else:
                            print(f"❌ {booth_number}: {company_name[:30]} -> Still Unknown")
        
        if retried > 0:
            self._save_cache()
        
        print(f"\nRetry summary: {retried} companies retried, {improved} improved")
        return {'retried': retried, 'improved': improved}

    def retry_unknown_company_names(self, venue_name):
        """Retry OpenAI analysis for companies that currently have unclear names"""
        companies = self.get_venue_companies(venue_name)
        
        retried = 0
        improved = 0
        
        for company in companies:
            company_name = company.get('name', '')
            booth_number = company.get('booth_number')
            
            # Check if company name looks like it needs improvement
            needs_retry = (
                not company_name or 
                company_name == 'Unknown Company' or
                len(company_name) < 3 or
                any(industry in company_name for industry in ['Financial Services', 'Engineering & Manufacturing', 'Banking & Finance'])
            )
            
            if needs_retry and booth_number:
                # Force a new analysis by removing from cache
                page_num = self._find_booth_page(booth_number)
                if page_num:
                    cache_key = f"company_{booth_number}_{page_num}_{os.path.getmtime(self.pdf_path) if self.pdf_path.exists() else 0}"
                    if cache_key in self.vision_cache:
                        del self.vision_cache[cache_key]
                    
                    # Get new result
                    new_name = self.extract_company_name_with_openai(booth_number)
                    retried += 1
                    
                    if new_name != "Unknown" and new_name != company_name:
                        improved += 1
                        print(f"✅ {booth_number}: '{company_name}' -> '{new_name}'")
                    else:
                        print(f"❌ {booth_number}: '{company_name}' -> No improvement")
        
        if retried > 0:
            self._save_cache()
        
        print(f"\nCompany name retry summary: {retried} companies retried, {improved} improved")
        return {'retried': retried, 'improved': improved}
    
    def _load_pdf(self):
        """Load the PDF file"""
        try:
            self.reader = PdfReader(str(self.pdf_path))
            self.total_pages = len(self.reader.pages)
        except Exception as e:
            raise Exception(f"Error loading PDF: {str(e)}")
    
    def get_page_text(self, page_number):
        """Extract text from a specific page (1-indexed)"""
        if page_number < 1 or page_number > self.total_pages:
            raise ValueError(f"Page number must be between 1 and {self.total_pages}")
        
        try:
            page = self.reader.pages[page_number - 1]  # Convert to 0-indexed
            text = page.extract_text()
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from page {page_number}: {str(e)}")
    

    
    def parse_company_table(self, page_number, venue_context=None):
        """Parse company information from a specific page with booth numbers and education level eligibility"""
        try:
            text = self.get_page_text(page_number)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            companies = []
            
            import re
            
            # Simplified parsing - just extract booth numbers and company names
            booth_data = {}
            orphaned_companies = []
            
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Skip headers and irrelevant lines
                if any(skip in line.lower() for skip in ['participating employers', 'day 1:', 'day 2:', 'hall', 'level', 'booth company sector']):
                    i += 1
                    continue
                
                # Look for booth numbers and extract company names
                booth_pattern = r'([A-Z]\d{2,3})'
                booth_matches = re.findall(booth_pattern, line)
                
                if booth_matches:
                    # Found booth number(s) in this line
                    for booth in booth_matches:
                        # Extract company name from the line (remove booth number and industry keywords)
                        company_name = line
                        
                        # Remove booth number
                        company_name = re.sub(r'[A-Z]\d{2,3}', '', company_name).strip()
                        
                        # Remove common industry keywords to isolate company name
                        industry_keywords = [
                            'Banking & Finance', 'Technology & IT', 'Consulting',
                            'Engineering & Manufacturing', 'Energy & Renewables',
                            'Public Sector', 'Pharmaceutical, Healthcare, Biomedical Sciences',
                            'Chemicals', 'Education', 'Luxury, Retail & Consumer Goods'
                        ]
                        
                        for keyword in industry_keywords:
                            company_name = company_name.replace(keyword, '').strip()
                        
                        # Clean up extra whitespace
                        company_name = ' '.join(company_name.split())
                        
                        if company_name:
                            booth_data[booth] = {
                                'company': company_name,
                                'raw_text': line,
                                'line_number': i
                            }
                        else:
                            # No company name on this line, mark for orphan matching
                            booth_data[booth] = {
                                'company': '',
                                'raw_text': line,
                                'line_number': i
                            }
                
                # Check for orphaned company names
                elif (any(indicator in line.lower() for indicator in ['pte', 'ltd', 'inc', 'corp', 'singapore']) 
                      and len(line) > 5):
                    orphaned_companies.append({
                        'company': line,
                        'line_number': i
                    })
                
                i += 1
            
            # Match orphaned companies to booths without company names
            booths_without_companies = [booth for booth, data in booth_data.items() if not data['company']]
            booths_without_companies.sort(key=lambda x: booth_data[x]['line_number'])
            orphaned_companies.sort(key=lambda x: x['line_number'])
            
            for i, booth in enumerate(booths_without_companies):
                if i < len(orphaned_companies):
                    booth_data[booth]['company'] = orphaned_companies[i]['company']
            
            # Create final company list with OpenAI parsing for both company name and industry
            for booth, data in booth_data.items():
                if data['company'] or booth:  # Process all booths, even without parsed company names
                    # Use OpenAI to extract clean company name from PDF layout
                    clean_company_name = self.extract_company_name_with_openai(booth, venue_context)
                    
                    # Use the clean name if available, otherwise fall back to parsed name
                    final_company_name = clean_company_name if clean_company_name and clean_company_name != "Unknown" else data.get('company', 'Unknown Company')
                    
                    # Use OpenAI to parse industry from the PDF layout
                    industry = self.determine_industry_with_openai(booth, final_company_name, venue_context)
                    education_level = self.determine_education_level(data.get('raw_text', ''), final_company_name, booth, venue_context)
                    
                    # Get user interaction data
                    user_interaction = self.get_user_interaction(booth)
                    
                    companies.append({
                        'name': final_company_name,
                        'booth_number': booth,
                        'education_level': education_level,
                        'industry': industry,
                        'visited': user_interaction['visited'],
                        'resume_shared': user_interaction['resume_shared'],
                        'apply_online': user_interaction['apply_online'],
                        'interested': user_interaction['interested'],
                        'comments': user_interaction['comments'],
                        'raw_text': data.get('raw_text', '')
                    })
            
            return companies
        except Exception as e:
            print(f"Error parsing companies from page {page_number}: {str(e)}")
            return []
    
    def get_venue_companies(self, venue_name):
        """Get companies for a specific venue based on page mappings"""
        venue_page_mappings = {
            # Day 1 venues
            'SRC Hall A': [11, 12],   # Pages after SRC Hall A map (page 10)
            'SRC Hall B': [14, 15],   # Pages after SRC Hall B map (page 13)
            'SRC Hall C': [17, 18],   # Pages after SRC Hall C map (page 16)
            'EA Atrium': [20, 21],    # Pages after EA Atrium map (page 19)
            
            # Day 2 venues
            'SRC Hall A Day 2': [23, 24],   # Pages after SRC Hall A Day 2 map (page 22)
            'SRC Hall B Day 2': [26, 27],   # Pages after SRC Hall B Day 2 map (page 25)
            'SRC Hall C Day 2': [29, 30],   # Pages after SRC Hall C Day 2 map (page 28)
            'EA Atrium Day 2': [32, 33, 34] # Pages after EA Atrium Day 2 map (page 31)
        }
        
        pages = venue_page_mappings.get(venue_name, [])
        all_companies = []
        
        for page_num in pages:
            try:
                companies = self.parse_company_table(page_num, venue_name)
                all_companies.extend(companies)
            except Exception as e:
                print(f"Warning: Could not parse companies from page {page_num}: {str(e)}")
                continue
        
        return all_companies
    
    def extract_company_name_with_openai(self, booth_number, venue_context=None):
        """Use OpenAI vision to extract clean company name from PDF layout"""
        
        if not OPENAI_AVAILABLE or not openai_client:
            return "Unknown"
        
        try:
            # Find which page contains this booth
            page_num = self._find_booth_page(booth_number, venue_context)
            if page_num is None:
                return "Unknown"
            
            # Check cache first (use company-specific cache key) - include venue context for Day 2
            cache_suffix = "_day2" if venue_context and "Day 2" in venue_context else ""
            cache_key = f"company_{booth_number}_{page_num}_{os.path.getmtime(self.pdf_path) if self.pdf_path.exists() else 0}{cache_suffix}"
            if cache_key in self.vision_cache:
                cached_result = self.vision_cache[cache_key]
                return cached_result
            
            # Analyze with OpenAI vision
            company_name = self._analyze_company_name_with_openai_vision(booth_number, page_num)
            
            if company_name:
                # Cache the result
                self.vision_cache[cache_key] = company_name
                self._save_cache()
                return company_name
            else:
                # Cache "Unknown" result to avoid retrying indefinitely
                self.vision_cache[cache_key] = "Unknown"
                self._save_cache()
                return "Unknown"
                
        except Exception:
            return "Unknown"

    def _analyze_company_name_with_openai_vision(self, booth_number, page_num, max_retries=3):
        """Use OpenAI vision to analyze company name from PDF layout"""
        
        for attempt in range(max_retries):
            try:
                # Convert PDF page to optimized image
                image_data = self._convert_pdf_page_to_image(page_num)
                if not image_data:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return "Unknown"
                
                # Create prompt for company name extraction
                prompt = f"""Look at this career fair page and find booth {booth_number}.

Extract the COMPANY NAME for this booth. The company name is the main business name, NOT the industry category.

For example:
- If you see "Financial ServicesA34 DRW Trading Group", the company name is "DRW Trading Group"
- If you see "Engineering & ManufacturingA15 Siemens", the company name is "Siemens"  
- If you see "ChemicalsA20 BASF Singapore", the company name is "BASF Singapore"

Look carefully around booth {booth_number} and extract ONLY the company/business name. Ignore industry labels like "Financial Services", "Engineering & Manufacturing", etc.

Respond with ONLY the clean company name, nothing else."""

                # Call OpenAI with optimized settings
                response = openai_client.chat.completions.create(
                    model="gpt-4o",  # Use full GPT-4o for better text extraction
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_data}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=100,  # Allow more tokens for company names
                    temperature=0.1,
                    timeout=20
                )
                
                # Parse and clean response
                company_name = response.choices[0].message.content.strip()
                
                # Basic validation - company name shouldn't be an industry
                industry_keywords = [
                    'Banking & Finance', 'Technology & IT', 'Consulting',
                    'Engineering & Manufacturing', 'Energy & Renewables',
                    'Public Sector', 'Pharmaceutical, Healthcare, Biomedical Sciences',
                    'Chemicals', 'Education', 'Luxury, Retail & Consumer Goods',
                    'Real Estate & Construction', 'Financial Services', 'Banks (Local/Asia)',
                    'Transport, Maritime', 'Healthcare'
                ]
                
                # If the response is just an industry keyword, it's not a valid company name
                if company_name in industry_keywords:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return "Unknown"
                
                # Basic validation - should have some text
                if len(company_name) > 2 and company_name.lower() not in ['unknown', 'n/a', 'none']:
                    return company_name
                
                # If no valid company name found on last attempt, return Unknown
                if attempt == max_retries - 1:
                    return "Unknown"
                
                # Otherwise retry
                time.sleep(2 ** attempt)
                continue
                
            except Exception as e:
                error_msg = str(e)
                
                # Handle rate limiting with exponential backoff
                if "rate_limit_exceeded" in error_msg or "429" in error_msg:
                    wait_time = (2 ** attempt) * 2
                    time.sleep(wait_time)
                    continue
                
                # Handle timeout errors
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    wait_time = (2 ** attempt) * 1
                    time.sleep(wait_time)
                    continue
                
                # For other errors, wait and retry if not the last attempt
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
        
        return "Unknown"

    def determine_industry_with_openai(self, booth_number, company_name, venue_context=None):
        """Use OpenAI vision to determine industry from PDF table layout"""
        
        if not OPENAI_AVAILABLE or not openai_client:
            return "Unknown"
        
        try:
            # Find which page contains this booth
            page_num = self._find_booth_page(booth_number, venue_context)
            if page_num is None:
                return "Unknown"
            
            # Check cache first (use industry-specific cache key) - include venue context for Day 2
            cache_suffix = "_day2" if venue_context and "Day 2" in venue_context else ""
            cache_key = f"industry_{booth_number}_{page_num}_{os.path.getmtime(self.pdf_path) if self.pdf_path.exists() else 0}{cache_suffix}"
            if cache_key in self.vision_cache:
                cached_result = self.vision_cache[cache_key]
                # Only return cached result if it's not "Unknown" - retry "Unknown" results
                if cached_result != "Unknown":
                    return cached_result
                # If cached result is "Unknown", we'll retry below
            
            # Analyze with OpenAI vision
            industry = self._analyze_industry_with_openai_vision(booth_number, company_name, page_num)
            
            if industry:
                # Cache the result (even if it's "Unknown" to avoid infinite retries)
                self.vision_cache[cache_key] = industry
                self._save_cache()
                return industry
            else:
                # Cache "Unknown" result to avoid retrying indefinitely
                self.vision_cache[cache_key] = "Unknown"
                self._save_cache()
                return "Unknown"
                
        except Exception:
            return "Unknown"
    
    def _analyze_industry_with_openai_vision(self, booth_number, company_name, page_num, max_retries=3):
        """Use OpenAI vision to analyze industry information from PDF layout"""
        
        for attempt in range(max_retries):
            try:
                # Convert PDF page to optimized image
                image_data = self._convert_pdf_page_to_image(page_num)
                if not image_data:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return "Unknown"
                
                # Create prompt for industry extraction
                prompt = f"""Look at this career fair page and find booth {booth_number} with company "{company_name}".

Find the industry category for this booth. The industry should be one of these categories:
- Banking & Finance
- Technology & IT
- Consulting  
- Engineering & Manufacturing
- Energy & Renewables
- Public Sector
- Pharmaceutical, Healthcare, Biomedical Sciences
- Chemicals
- Education
- Luxury, Retail & Consumer Goods
- Real Estate & Construction
- Financial Services
- Banks (Local/Asia)
- Transport, Maritime
- Healthcare (standalone)

The industry might be:
- On the same line as the booth number (like "Financial ServicesA33")
- On a line above or below the booth
- As a section header that applies to multiple booths
- In a table column next to the company name

Look carefully at the layout around booth {booth_number} and respond with ONLY the exact industry name from the list above, or "Unknown" if no clear industry is shown."""

                # Call OpenAI with optimized settings - using full GPT-4o for better layout understanding
                response = openai_client.chat.completions.create(
                    model="gpt-4o",  # Full GPT-4o for better complex layout parsing
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_data}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=50,  # Keep concise for industry names
                    temperature=0.1,
                    timeout=20  # Increased timeout for more complex model
                )
                
                # Parse and validate response
                industry = response.choices[0].message.content.strip()
                
                # Validate against known industries (including new categories from page 12)
                valid_industries = [
                    'Banking & Finance', 'Technology & IT', 'Consulting',
                    'Engineering & Manufacturing', 'Energy & Renewables',
                    'Public Sector', 'Pharmaceutical, Healthcare, Biomedical Sciences',
                    'Chemicals', 'Education', 'Luxury, Retail & Consumer Goods',
                    'Real Estate & Construction', 'Financial Services', 'Banks (Local/Asia)',
                    'Transport, Maritime', 'Healthcare (standalone)'
                ]
                
                # Check for exact matches first
                for valid_industry in valid_industries:
                    if valid_industry == industry.strip():
                        return valid_industry
                
                # Check for partial matches
                for valid_industry in valid_industries:
                    if valid_industry.lower() in industry.lower():
                        return valid_industry
                
                # If no match found on last attempt, return Unknown
                if attempt == max_retries - 1:
                    return "Unknown"
                
                # Otherwise retry
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
                
            except Exception as e:
                error_msg = str(e)
                
                # Handle rate limiting with exponential backoff
                if "rate_limit_exceeded" in error_msg or "429" in error_msg:
                    wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                    time.sleep(wait_time)
                    continue
                
                # Handle timeout errors
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    wait_time = (2 ** attempt) * 1  # 1, 2, 4 seconds
                    time.sleep(wait_time)
                    continue
                
                # For other errors, wait and retry if not the last attempt
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
        
        return "Unknown"
    
    def determine_education_level(self, raw_line, company_name, booth_number=None, venue_context=None):
        """Determine education level using OpenAI vision analysis with caching"""
        
        if not OPENAI_AVAILABLE or not openai_client:
            return "Unknown"
        
        try:
            # Find which page contains this booth
            page_num = self._find_booth_page(booth_number, venue_context)
            if page_num is None:
                return "Unknown"
            
            # Check cache first - include venue context in cache key for Day 2
            cache_suffix = "_day2" if venue_context and "Day 2" in venue_context else ""
            cache_key = self._get_cache_key(booth_number, page_num) + cache_suffix
            if cache_key in self.vision_cache:
                return self.vision_cache[cache_key]
            
            # Analyze with OpenAI vision
            education_level = self._analyze_with_openai_vision(booth_number, page_num)
            
            if education_level:
                # Cache the result
                self.vision_cache[cache_key] = education_level
                self._save_cache()
                return education_level
            else:
                return "Unknown"
                
        except Exception as e:
            return "Unknown"
    

    
    def _find_booth_page(self, booth_number, venue_context=None):
        """Find which page contains the given booth number"""
        if not booth_number:
            return None
            
        # Extract booth number for more precise mapping
        booth_prefix = booth_number[0]
        try:
            booth_num = int(booth_number[1:])
        except:
            booth_num = 0
        
        # If we have venue context (Day 2), use Day 2 pages
        if venue_context and "Day 2" in venue_context:
            # Day 2 booth mappings
            if booth_prefix == 'A':
                if booth_num <= 22:
                    return 23  # A01-A22 on page 23 (Day 2)
                else:
                    return 24  # A23+ on page 24 (Day 2)
            elif booth_prefix == 'B':
                return 26  # SRC Hall B Day 2
            elif booth_prefix == 'C':
                return 29  # SRC Hall C Day 2  
            elif booth_prefix == 'D':
                return 32  # EA Atrium Day 2
        else:
            # Day 1 booth mappings (default)
            if booth_prefix == 'A':
                if booth_num <= 22:
                    return 11  # A01-A22 on page 11 (Day 1)
                else:
                    return 12  # A23-A38 on page 12 (Day 1)
            elif booth_prefix == 'B':
                return 14  # SRC Hall B Day 1
            elif booth_prefix == 'C':
                return 17  # SRC Hall C Day 1
            elif booth_prefix == 'D':
                return 20  # EA Atrium Day 1
        
        return None
    
    def _analyze_with_openai_vision(self, booth_number, page_num, max_retries=3):
        """Use OpenAI vision to analyze education level icons with retries"""
        
        for attempt in range(max_retries):
            try:
                # Convert PDF page to optimized image
                image_data = self._convert_pdf_page_to_image(page_num)
                if not image_data:
                    continue
                
                # Create optimized prompt
                prompt = f"""Look carefully at this career fair page and find booth {booth_number}.

Each booth has a small briefcase icon next to it. The COLOR of the briefcase is critical:

- LIGHT PINK briefcase (pale/soft pink) = "Undergraduate" only
- DARK PINK briefcase (deeper/richer pink) = "Both" undergraduate and postgraduate  
- ORANGE briefcase = "Postgraduate" only

Compare the briefcase color at booth {booth_number} to nearby booths. Some booths like A01, A02, A03, A10, A15 have DARK PINK briefcases (Both), while booths like A04, A05, A11 have LIGHT PINK briefcases (Undergraduate only).

What color is the briefcase at booth {booth_number}? Respond with exactly one word: "Undergraduate", "Postgraduate", or "Both"."""

                # Call OpenAI with optimized settings
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Cost-effective vision model
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_data}",
                                        "detail": "high"  # Use high detail for better color analysis
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=5,  # Minimal tokens needed
                    temperature=0.1,  # Consistent responses
                    timeout=10  # 10 second timeout
                )
                
                # Parse and validate response
                classification = response.choices[0].message.content.strip()
                
                # Validate response
                valid_responses = ["Undergraduate", "Postgraduate", "Both"]
                for valid_response in valid_responses:
                    if valid_response.lower() in classification.lower():
                        return valid_response
                
                # If response is unclear, try again
                if attempt < max_retries - 1:
                    continue
                
            except Exception as e:
                error_msg = str(e)
                
                # Handle rate limiting with exponential backoff
                if "rate_limit_exceeded" in error_msg or "429" in error_msg:
                    wait_time = (2 ** attempt) * 1  # 1, 2, 4 seconds
                    time.sleep(wait_time)
                    continue
                
                # For other errors, wait a bit and retry if not the last attempt
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return None
    
    def _convert_pdf_page_to_image(self, page_num):
        """Convert PDF page to base64 image with optimization"""
        try:
            import fitz  # PyMuPDF
            
            # Open PDF and get page
            doc = fitz.open(str(self.pdf_path))
            page = doc[page_num - 1]  # Convert to 0-indexed
            
            # Use higher resolution for better color detection
            mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for better color analysis
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PNG bytes
            img_data = pix.tobytes("png")
            doc.close()
            
            # Optimize image size for token efficiency
            image = Image.open(io.BytesIO(img_data))
            
            # Resize if too large (reduce tokens)
            max_width = 1200
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            output = io.BytesIO()
            image.save(output, format='PNG', optimize=True)
            img_bytes = output.getvalue()
            
            # Convert to base64
            base64_image = base64.b64encode(img_bytes).decode('utf-8')
            
            return base64_image
            
        except Exception:
            return None
