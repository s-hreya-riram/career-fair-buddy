"""
OpenAI integration service
Handles all OpenAI API calls for vision analysis with retry logic
"""
import base64
import io
import time
import random
from typing import Optional, Dict, Any
from PIL import Image
import fitz  # PyMuPDF

from .config import Config
from .cache_manager import CacheManager
from .utils import exponential_backoff_wait, is_valid_education_level, is_valid_industry


class OpenAIService:
    """Service for OpenAI API interactions with caching and retry logic"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.client = None
        self.available = self._setup_client()
    
    def _setup_client(self) -> bool:
        """Set up OpenAI client"""
        if not Config.OPENAI_API_KEY:
            print("❌ OpenAI API key not found")
            return False
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
            print("✅ OpenAI client initialized successfully")
            return True
        except ImportError as e:
            print(f"❌ OpenAI package not available: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.available and self.client is not None
    
    def analyze_education_level(
        self, 
        booth_number: str, 
        page_num: int, 
        pdf_path: str,
        is_day2: bool = False
    ) -> str:
        """Analyze education level for a booth using vision API"""
        if not self.is_available():
            return "Unknown"
        
        # Check cache first
        cached = self.cache_manager.get_education_level(booth_number, page_num, is_day2)
        if cached:
            return cached
        
        # Analyze with OpenAI
        result = self._analyze_education_with_vision(booth_number, page_num, pdf_path)
        
        if result and is_valid_education_level(result):
            self.cache_manager.set_education_level(booth_number, page_num, result, is_day2)
            self.cache_manager.save_cache()
            return result
        
        # Cache unknown result to avoid re-analyzing
        self.cache_manager.set_education_level(booth_number, page_num, "Unknown", is_day2)
        self.cache_manager.save_cache()
        return "Unknown"
    
    def analyze_company_name(
        self, 
        booth_number: str, 
        page_num: int, 
        pdf_path: str,
        is_day2: bool = False
    ) -> str:
        """Analyze company name for a booth using vision API"""
        if not self.is_available():
            return "Unknown"
        
        # Check cache first
        cached = self.cache_manager.get_company_name(booth_number, page_num, is_day2)
        if cached:
            return cached
        
        # Analyze with OpenAI
        result = self._analyze_company_with_vision(booth_number, page_num, pdf_path)
        
        if result and result != "Unknown":
            self.cache_manager.set_company_name(booth_number, page_num, result, is_day2)
        else:
            self.cache_manager.set_company_name(booth_number, page_num, "Unknown", is_day2)
        
        self.cache_manager.save_cache()
        return result or "Unknown"
    
    def analyze_industry(
        self, 
        booth_number: str, 
        company_name: str,
        page_num: int, 
        pdf_path: str,
        is_day2: bool = False
    ) -> str:
        """Analyze industry for a booth using vision API"""
        if not self.is_available():
            return "Unknown"
        
        # Check cache first
        cached = self.cache_manager.get_industry(booth_number, page_num, is_day2)
        if cached:
            return cached
        
        # Analyze with OpenAI
        result = self._analyze_industry_with_vision(booth_number, company_name, page_num, pdf_path)
        
        if result and is_valid_industry(result):
            self.cache_manager.set_industry(booth_number, page_num, result, is_day2)
        else:
            self.cache_manager.set_industry(booth_number, page_num, "Unknown", is_day2)
        
        self.cache_manager.save_cache()
        return result or "Unknown"
    
    def analyze_company_website(
        self, 
        booth_number: str, 
        company_name: str,
        page_num: int,
        is_day2: bool = False
    ) -> str:
        """Analyze company website using OpenAI API"""
        if not self.is_available():
            return ""
        
        # Check cache first
        cached = self.cache_manager.get_company_website(booth_number, page_num, is_day2)
        if cached:
            return cached
        
        # Analyze with OpenAI
        result = self._analyze_website_with_ai(company_name)
        
        # Cache the result (even if empty)
        self.cache_manager.set_company_website(booth_number, page_num, result, is_day2)
        self.cache_manager.save_cache()
        return result or ""
    
    def _analyze_education_with_vision(self, booth_number: str, page_num: int, pdf_path: str) -> Optional[str]:
        """Analyze education level using OpenAI vision with retry logic"""
        for attempt in range(Config.OPENAI_MAX_RETRIES):
            try:
                # Convert PDF page to image
                image_data = self._convert_pdf_page_to_image(page_num, pdf_path)
                if not image_data:
                    continue
                
                prompt = f"""Look carefully at this career fair page and find booth {booth_number}.

Each booth has a small briefcase icon next to it. The COLOR of the briefcase is critical:

- LIGHT PINK briefcase (pale/soft pink) = "Undergraduate" only
- DARK PINK briefcase (deeper/richer pink) = "Both" undergraduate and postgraduate  
- ORANGE briefcase = "Postgraduate" only

Compare the briefcase color at booth {booth_number} to nearby booths. Some booths like A01, A02, A03, A10, A15 have DARK PINK briefcases (Both), while booths like A04, A05, A11 have LIGHT PINK briefcases (Undergraduate only).

What color is the briefcase at booth {booth_number}? Respond with exactly one word: "Undergraduate", "Postgraduate", or "Both"."""
                
                response = self.client.chat.completions.create(
                    model=Config.OPENAI_MODEL_MINI,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }],
                    max_tokens=5,
                    temperature=0.1,
                    timeout=Config.OPENAI_TIMEOUT
                )
                
                classification = response.choices[0].message.content.strip()
                
                # Validate response
                for valid_response in Config.EDUCATION_LEVELS:
                    if valid_response.lower() in classification.lower():
                        return valid_response
                
                # If response is unclear, try again
                if attempt < Config.OPENAI_MAX_RETRIES - 1:
                    continue
                
            except Exception as e:
                if self._should_retry(e, attempt):
                    self._handle_retry_wait(e, attempt)
                    continue
                break
        
        return None
    
    def _analyze_company_with_vision(self, booth_number: str, page_num: int, pdf_path: str) -> Optional[str]:
        """Analyze company name using OpenAI vision with retry logic"""
        for attempt in range(Config.OPENAI_MAX_RETRIES):
            try:
                image_data = self._convert_pdf_page_to_image(page_num, pdf_path)
                if not image_data:
                    continue
                
                prompt = f"""Look at this career fair page and find booth {booth_number}.

Extract the COMPANY NAME for this booth. The company name is the main business name, NOT the industry category.

For example:
- If you see "Financial ServicesA34 DRW Trading Group", the company name is "DRW Trading Group"
- If you see "Engineering & ManufacturingA15 Siemens", the company name is "Siemens"  
- If you see "ChemicalsA20 BASF Singapore", the company name is "BASF Singapore"

Look carefully around booth {booth_number} and extract ONLY the company/business name. Ignore industry labels like "Financial Services", "Engineering & Manufacturing", etc.

Respond with ONLY the clean company name, nothing else."""
                
                response = self.client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }],
                    max_tokens=100,
                    temperature=0.1,
                    timeout=Config.OPENAI_TIMEOUT
                )
                
                company_name = response.choices[0].message.content.strip()
                
                # Basic validation - company name shouldn't be an industry
                if company_name in Config.VALID_INDUSTRIES:
                    if attempt < Config.OPENAI_MAX_RETRIES - 1:
                        continue
                    return "Unknown"
                
                if len(company_name) > 2 and company_name.lower() not in ['unknown', 'n/a', 'none']:
                    return company_name
                
                if attempt < Config.OPENAI_MAX_RETRIES - 1:
                    continue
                
            except Exception as e:
                if self._should_retry(e, attempt):
                    self._handle_retry_wait(e, attempt)
                    continue
                break
        
        return None
    
    def _analyze_industry_with_vision(self, booth_number: str, company_name: str, page_num: int, pdf_path: str) -> Optional[str]:
        """Analyze industry using OpenAI vision with retry logic"""
        for attempt in range(Config.OPENAI_MAX_RETRIES):
            try:
                image_data = self._convert_pdf_page_to_image(page_num, pdf_path)
                if not image_data:
                    continue
                
                industry_list = "\\n- ".join(Config.VALID_INDUSTRIES)
                prompt = f"""Look at this career fair page and find booth {booth_number} with company "{company_name}".

Find the industry category for this booth. The industry should be one of these categories:
- {industry_list}

The industry might be:
- On the same line as the booth number (like "Financial ServicesA33")
- On a line above or below the booth
- As a section header that applies to multiple booths
- In a table column next to the company name

Look carefully at the layout around booth {booth_number} and respond with ONLY the exact industry name from the list above, or "Unknown" if no clear industry is shown."""
                
                response = self.client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }],
                    max_tokens=50,
                    temperature=0.1,
                    timeout=Config.OPENAI_TIMEOUT
                )
                
                industry = response.choices[0].message.content.strip()
                
                # Check for exact matches first
                for valid_industry in Config.VALID_INDUSTRIES:
                    if valid_industry == industry.strip():
                        return valid_industry
                
                # Check for partial matches
                for valid_industry in Config.VALID_INDUSTRIES:
                    if valid_industry.lower() in industry.lower():
                        return valid_industry
                
                if attempt < Config.OPENAI_MAX_RETRIES - 1:
                    continue
                
            except Exception as e:
                if self._should_retry(e, attempt):
                    self._handle_retry_wait(e, attempt)
                    continue
                break
        
        return None
    
    def _analyze_website_with_ai(self, company_name: str) -> Optional[str]:
        """Analyze company website using OpenAI text completion with retry logic"""
        for attempt in range(Config.OPENAI_MAX_RETRIES):
            try:
                prompt = f"""Find the official website URL for the company "{company_name}".

Context: This company is participating in the NUS Career Fair 2025 in Singapore. Most companies are either:
- Based in Singapore 
- Major multinational companies with Singapore operations
- Regional companies operating in Southeast Asia

Requirements:
- Return ONLY the main website URL (e.g., https://company.com)
- Prefer the Singapore/regional website if multiple exist
- If the company has multiple business units, return the main corporate website
- Do not include specific page URLs (careers, about, etc.) - just the homepage
- If uncertain between multiple companies with similar names, prefer the larger/more established one

Examples:
- "DBS Bank" → "https://www.dbs.com.sg"
- "Grab" → "https://www.grab.com" 
- "Shopee" → "https://shopee.sg"
- "Google" → "https://www.google.com"

Company: {company_name}
Website URL:"""
                
                response = self.client.chat.completions.create(
                    model=Config.OPENAI_MODEL_MINI,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.1,
                    timeout=Config.OPENAI_TIMEOUT
                )
                
                website = response.choices[0].message.content.strip()
                
                # Validate URL format
                if self._is_valid_url(website):
                    return website
                
                if attempt < Config.OPENAI_MAX_RETRIES - 1:
                    continue
                
            except Exception as e:
                if self._should_retry(e, attempt):
                    self._handle_retry_wait(e, attempt)
                    continue
                break
        
        return None
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url:
            return False
        
        # Basic URL validation
        url = url.strip()
        
        # Must start with http or https
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        # Must contain a domain
        if '.' not in url:
            return False
        
        # Must not contain spaces
        if ' ' in url:
            return False
        
        # Must be reasonable length
        if len(url) > 200:
            return False
        
        return True
    
    def _convert_pdf_page_to_image(self, page_num: int, pdf_path: str) -> Optional[str]:
        """Convert PDF page to base64 image"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]  # Convert to 0-indexed
            
            # Use higher resolution for better analysis
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat)
            
            img_data = pix.tobytes("png")
            doc.close()
            
            # Optimize image size
            image = Image.open(io.BytesIO(img_data))
            
            max_width = 1200
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            image.save(output, format='PNG', optimize=True)
            img_bytes = output.getvalue()
            
            return base64.b64encode(img_bytes).decode('utf-8')
            
        except Exception as e:
            print(f"Error converting PDF page {page_num}: {e}")
            return None
    
    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if we should retry based on error type and attempt number"""
        if attempt >= Config.OPENAI_MAX_RETRIES - 1:
            return False
        
        error_msg = str(error).lower()
        
        # Always retry rate limits, timeouts, and API errors
        retry_indicators = [
            "rate_limit_exceeded", "429", "timeout", "timed out", 
            "api", "openai", "connection", "network"
        ]
        
        return any(indicator in error_msg for indicator in retry_indicators)
    
    def _handle_retry_wait(self, error: Exception, attempt: int) -> None:
        """Handle waiting between retries based on error type"""
        error_msg = str(error).lower()
        
        if "rate_limit_exceeded" in error_msg or "429" in error_msg:
            # Longer wait for rate limits
            wait_time = (2 ** attempt) * 5 + random.uniform(0, 5)
        elif "timeout" in error_msg or "timed out" in error_msg:
            # Moderate wait for timeouts
            wait_time = (2 ** attempt) * 2 + random.uniform(0, 2)
        else:
            # Standard exponential backoff
            wait_time = (2 ** attempt) + random.uniform(0, 2)
        
        print(f"Retrying in {wait_time:.1f}s (attempt {attempt + 1}/{Config.OPENAI_MAX_RETRIES})")
        time.sleep(wait_time)
    
    def analyze_resume_match(self, resume_content: str, companies: list, user_preferences: str = "") -> list:
        """Analyze resume for company matches"""
        if not self.is_available():
            return []
        
        try:
            # Limit companies for performance
            limited_companies = companies[:150]
            
            # Create company summaries
            company_summaries = []
            for i, company in enumerate(limited_companies):
                summary = f"{i+1}. {company['name']} (Booth {company['booth_number']}) - {company['industry']} - {company['education_level']} - {company.get('venue', 'Unknown')}"
                company_summaries.append(summary)
            
            companies_text = "\\n".join(company_summaries)
            
            prompt = f"""You are a career counselor helping a student find the best company matches at a career fair.

STUDENT PROFILE:
{resume_content[:2500]}  

USER PREFERENCES:
{user_preferences}

AVAILABLE COMPANIES:
{companies_text}

Analyze the profile and preferences, then recommend the TOP 8 companies that would be the best matches. Consider industry alignment, education requirements, skills relevance, and career goals.

Respond ONLY with valid JSON:
{{
  "matches": [
    {{
      "company_name": "Company Name",
      "booth_number": "A01", 
      "venue": "SRC Hall A",
      "match_percentage": 85,
      "explanation": "Brief explanation of match",
      "alignment_factors": ["Factor 1", "Factor 2"]
    }}
  ]
}}"""
            
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL_MINI,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.2,
                timeout=20
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_text = response_text[json_start:json_end]
                    result = json.loads(json_text)
                    
                    # Enhance matches with full company data
                    enhanced_matches = []
                    for match in result.get('matches', []):
                        for company in companies:
                            if (company['name'] == match['company_name'] or 
                                company['booth_number'] == match['booth_number']):
                                enhanced_match = {
                                    **company,
                                    'match_percentage': match.get('match_percentage', 0),
                                    'explanation': match.get('explanation', ''),
                                    'alignment_factors': match.get('alignment_factors', [])
                                }
                                enhanced_matches.append(enhanced_match)
                                break
                    
                    return enhanced_matches
            except json.JSONDecodeError:
                pass
            
            return []
            
        except Exception as e:
            print(f"Error analyzing resume match: {e}")
            return []
