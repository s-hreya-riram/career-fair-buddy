import streamlit as st
import sys
import os
from pathlib import Path
from PIL import Image
import tempfile
import io

# Page configuration for better mobile experience
st.set_page_config(
    page_title="Career Fair Buddy",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://github.com/your-repo/career-fair-buddy',
        'Report a bug': 'https://github.com/your-repo/career-fair-buddy/issues',
        'About': '# Career Fair Buddy\nYour AI-powered career fair companion!'
    }
)

# Add custom CSS for mobile responsiveness and dark mode compatibility
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .stColumns > div {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        .stTextInput > div > div > input {
            font-size: 16px !important; /* Prevents zoom on iOS */
        }
        
        .stSelectbox > div > div > select {
            font-size: 16px !important;
        }
        
        .stCheckbox > label {
            font-size: 14px !important;
        }
        
        .company-card {
            margin-bottom: 1rem;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid rgba(49, 51, 63, 0.2);
            background-color: rgba(0, 0, 0, 0.02);
        }
        
        [data-theme="dark"] .company-card {
            background-color: rgba(255, 255, 255, 0.02);
            border-color: rgba(255, 255, 255, 0.1);
        }
    }
    
    /* Desktop styles */
    @media (min-width: 769px) {
        .company-card {
            margin-bottom: 1rem;
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid rgba(49, 51, 63, 0.2);
            background-color: rgba(0, 0, 0, 0.02);
        }
        
        [data-theme="dark"] .company-card {
            background-color: rgba(255, 255, 255, 0.02);
            border-color: rgba(255, 255, 255, 0.1);
        }
    }
    
    /* Better button styling */
    .stButton > button {
        width: 100%;
        border-radius: 6px;
        font-weight: 500;
        border: none;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Improved checkbox styling */
    .stCheckbox {
        padding: 0.25rem 0;
    }
    
    /* Better spacing for mobile */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Improve readability */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    /* Make tables more readable on mobile */
    .stTable {
        font-size: 0.9rem;
    }
    
    @media (max-width: 768px) {
        .stTable {
            font-size: 0.8rem;
        }
    }
    
    /* Improve divider visibility in dark mode */
    [data-theme="dark"] hr {
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Better card styling for mobile view */
    .mobile-card {
        background: var(--background-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Responsive text sizing */
    @media (max-width: 480px) {
        .stMarkdown h1 {
            font-size: 1.5rem !important;
        }
        .stMarkdown h2 {
            font-size: 1.3rem !important;
        }
        .stMarkdown h3 {
            font-size: 1.1rem !important;
        }
    }
    
    /* Hidden device detection element */
    .device-detector {
        display: none;
    }
</style>

<script>
// Device detection script
function detectDevice() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    let deviceType = 'desktop';
    
    if (width <= 768) {
        deviceType = 'mobile';
    } else if (width <= 1024 && isTouchDevice) {
        deviceType = 'tablet';
    }
    
    // Store device type in sessionStorage
    sessionStorage.setItem('deviceType', deviceType);
    
    // Create a hidden element to communicate with Streamlit
    const detector = document.createElement('div');
    detector.className = 'device-detector';
    detector.setAttribute('data-device-type', deviceType);
    detector.textContent = deviceType;
    document.body.appendChild(detector);
    
    // Trigger a custom event
    window.dispatchEvent(new CustomEvent('deviceDetected', { detail: deviceType }));
}

// Run detection when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', detectDevice);
} else {
    detectDevice();
}

// Re-run detection on window resize
window.addEventListener('resize', detectDevice);
</script>
""", unsafe_allow_html=True)

# Add the current directory to the path to import our PDF reader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import CareerFairPDFReader

# Try to import PyMuPDF (fitz), which doesn't require external dependencies
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except Exception as e:
    PYMUPDF_AVAILABLE = False
    PYMUPDF_ERROR = str(e)

class CareerFairApp:
    def __init__(self):
        """Initialize the Career Fair Streamlit App"""
        self.pdf_path = "data/nus-career-fest-2025-student-event-guide-ay2526-sem-1.pdf"
        self.pdf_reader = None
        self.init_pdf_reader()
    
    def init_pdf_reader(self):
        """Initialize the PDF reader"""
        try:
            self.pdf_reader = CareerFairPDFReader(self.pdf_path)
        except Exception as e:
            st.error(f"Error loading PDF: {str(e)}")
            st.stop()
    
    def is_mobile_device(self):
        """
        Enhanced mobile device detection using multiple signals.
        """
        # Initialize session state for device detection if not exists
        if 'mobile_override' not in st.session_state:
            # Try to automatically detect mobile devices on first visit
            auto_detected = self._auto_detect_mobile()
            st.session_state.mobile_override = auto_detected
            if auto_detected:
                st.session_state.auto_detection_message = "🤖 Automatically detected mobile device!"
        
        return st.session_state.get('mobile_override', False)
    
    def setup_mobile_toggle(self):
        """
        Set up the mobile mode toggle in the sidebar. Should only be called once.
        """
        # Add the mobile mode toggle in the sidebar for easy access
        with st.sidebar:
            st.divider()
            st.markdown("### 📱 Layout")
            
            # Show auto-detection message if it exists
            if 'auto_detection_message' in st.session_state:
                st.success(st.session_state.auto_detection_message)
                # Clear the message after showing it once
                del st.session_state.auto_detection_message
            
            mobile_override = st.toggle(
                "Mobile Mode", 
                value=st.session_state.get('mobile_override', False),
                help="Toggle for mobile-optimized card layouts vs desktop table view",
                key="mobile_mode_toggle"
            )
            
            if mobile_override != st.session_state.get('mobile_override', False):
                st.session_state.mobile_override = mobile_override
                if mobile_override:
                    st.success("📱 Mobile layout enabled!")
                else:
                    st.success("💻 Desktop layout enabled!")
                st.rerun()
    
    def _auto_detect_mobile(self):
        """
        Attempt to automatically detect mobile devices using JavaScript.
        """
        try:
            # Use HTML component with JavaScript to detect device type
            device_detection_html = """
            <script>
            function detectMobileDevice() {
                // Check multiple signals for mobile detection
                const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
                const isSmallScreen = window.innerWidth <= 768;
                const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
                
                const isMobileDevice = isMobile || (isSmallScreen && isTouchDevice);
                
                // Store in localStorage for persistence
                localStorage.setItem('deviceIsMobile', isMobileDevice.toString());
                
                // Also store detailed info for debugging
                const deviceInfo = {
                    userAgent: navigator.userAgent,
                    screenWidth: window.innerWidth,
                    screenHeight: window.innerHeight,
                    isTouchDevice: isTouchDevice,
                    isMobileUserAgent: isMobile,
                    isSmallScreen: isSmallScreen,
                    finalResult: isMobileDevice
                };
                
                localStorage.setItem('deviceInfo', JSON.stringify(deviceInfo));
                
                return isMobileDevice;
            }
            
            // Run detection
            const isMobile = detectMobileDevice();
            
            // Display result (hidden)
            document.body.innerHTML = '<div style="display:none;">Mobile: ' + isMobile + '</div>';
            </script>
            """
            
            # Execute the JavaScript (this runs in the browser)
            st.components.v1.html(device_detection_html, height=0)
            
            # For now, return False as we can't easily get the JavaScript result back
            # In a production app, you might use streamlit-js or other methods
            return False
            
        except Exception:
            return False  # Safe fallback
    
    def convert_pdf_page_to_image(self, page_number):
        """Convert a specific PDF page to an image using PyMuPDF"""
        if not PYMUPDF_AVAILABLE:
            return None
            
        try:
            # Open the PDF with PyMuPDF
            doc = fitz.open(self.pdf_path)
            
            # Get the specific page (0-indexed)
            page = doc[page_number - 1]
            
            # Render page to pixmap (image)
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # Close the document
            doc.close()
            
            return image
        except Exception as e:
            st.error(f"Error converting page {page_number} to image: {str(e)}")
            return None
    
    def display_map_page(self, page_number, title):
        """Display a map page with title"""
        st.subheader(title)
        
        if not PYMUPDF_AVAILABLE:
            st.error("⚠️ PyMuPDF not available for PDF to image conversion")
            st.info("""
            **To view PDF pages as images, PyMuPDF should be installed:**
            
            ```
            pip install PyMuPDF
            ```
            """)
            
            # Show text content instead
            st.write("**Text content from this page:**")
            try:
                text = self.pdf_reader.get_page_text(page_number)
                st.text_area(f"Page {page_number} Content", text, height=400, disabled=True)
            except Exception as e:
                st.error(f"Error extracting text: {str(e)}")
            return
        
        with st.spinner(f"Loading page {page_number}..."):
            image = self.convert_pdf_page_to_image(page_number)
            
            if image:
                # Display the image
                st.image(image, caption=f"Page {page_number} - {title}", width='stretch')
                
                # Add download button for the image
                img_buffer = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                image.save(img_buffer.name, 'PNG')
                
                with open(img_buffer.name, 'rb') as f:
                    st.download_button(
                        label=f"Download {title} Map",
                        data=f.read(),
                        file_name=f"career_fair_map_page_{page_number}.png",
                        mime="image/png"
                    )
                
                # Clean up temp file
                os.unlink(img_buffer.name)
            else:
                st.error(f"Could not load page {page_number}")
                # Fallback to text content
                st.write("**Text content from this page:**")
                try:
                    text = self.pdf_reader.get_page_text(page_number)
                    st.text_area(f"Page {page_number} Content", text, height=300, disabled=True)
                except Exception as e:
                    st.error(f"Error extracting text: {str(e)}")
    
    def display_page_text(self, page_number):
        """Display text content from a page in an expandable section"""
        with st.expander(f"View text content from page {page_number}"):
            try:
                text = self.pdf_reader.get_page_text(page_number)
                st.text_area("Page Content", text, height=200, disabled=True)
            except Exception as e:
                st.error(f"Error extracting text: {str(e)}")
    
    def display_company_table(self, venue_name):
        """Display company listings for a specific venue with education level filtering"""
        st.subheader("🏢 Companies at this Venue")
        
        # Get company data for this venue
        companies = self.pdf_reader.get_venue_companies(venue_name)
        
        if not companies:
            st.info("No company data found for this venue. Please check the PDF structure.")
            return
        
        # Education level filter
        st.subheader("🎓 Filter by Education Level Eligibility")
        
        # Create standardized education level options
        education_options = ["All", "Undergraduate", "Postgraduate"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_levels = st.multiselect(
                "Select education levels:",
                options=education_options,
                default=["All"],
                help="Filter companies based on whether they're open to undergraduates, postgraduates, or both. Companies marked as 'Both' will appear when either level is selected.",
                key=f"education_filter_{venue_name.replace(' ', '_').replace('-', '_')}"
            )
        
        with col2:
            # Industry filter
            available_industries = list(set([company.get('industry', 'Not specified') for company in companies]))
            available_industries.sort()
            industry_filter_options = ["All"] + available_industries
            
            selected_industries = st.multiselect(
                "Select industries:",
                options=industry_filter_options,
                default=["All"],
                help="Filter companies by industry sector",
                key=f"industry_filter_{venue_name.replace(' ', '_').replace('-', '_')}"
            )
        
        # Filter companies based on selection
        filtered_companies = companies
        
        # Enhanced education level filtering logic
        if "All" not in selected_levels and selected_levels:
            def matches_education_filter(company):
                company_edu_level = company.get('education_level', 'Unknown')
                
                # If company accepts "Both", it should appear for any selection
                if company_edu_level == "Both":
                    return True
                
                # If company has specific level, check if it matches selection
                if company_edu_level in selected_levels:
                    return True
                
                return False
            
            filtered_companies = [
                company for company in filtered_companies 
                if matches_education_filter(company)
            ]
        
        if "All" not in selected_industries and selected_industries:
            filtered_companies = [
                company for company in filtered_companies 
                if company.get('industry', 'Not specified') in selected_industries
            ]
        
        # Quick action filters
        st.subheader("🎯 Quick Action Filters")
        filter_cols = st.columns(5)
        
        # Create unique filter key base
        filter_key_base = venue_name.replace(' ', '_').replace('-', '_')
        
        with filter_cols[0]:
            if st.button("Show Interested", key=f"filter_interested_{filter_key_base}"):
                st.session_state[f"show_interested_{filter_key_base}"] = True
                st.rerun()
        
        with filter_cols[1]:
            if st.button("Show Unvisited", key=f"filter_unvisited_{filter_key_base}"):
                st.session_state[f"show_unvisited_{filter_key_base}"] = True
                st.rerun()
        
        with filter_cols[2]:
            if st.button("Show Need Resume", key=f"filter_need_resume_{filter_key_base}"):
                st.session_state[f"show_need_resume_{filter_key_base}"] = True
                st.rerun()
        
        with filter_cols[3]:
            if st.button("Show Apply Online", key=f"filter_apply_online_{filter_key_base}"):
                st.session_state[f"show_apply_online_{filter_key_base}"] = True
                st.rerun()
        
        with filter_cols[4]:
            if st.button("Show All", key=f"filter_all_{filter_key_base}"):
                # Clear all filter states
                for key in [f"show_interested_{filter_key_base}", f"show_unvisited_{filter_key_base}", f"show_need_resume_{filter_key_base}", f"show_apply_online_{filter_key_base}"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        # Apply quick filters
        if st.session_state.get(f"show_interested_{filter_key_base}", False):
            st.info("🔍 Showing only companies marked as interested")
            filtered_companies = [comp for comp in filtered_companies if comp.get('interested', False)]
        elif st.session_state.get(f"show_unvisited_{filter_key_base}", False):
            st.info("🔍 Showing only unvisited companies")
            filtered_companies = [comp for comp in filtered_companies if not comp.get('visited', False)]
        elif st.session_state.get(f"show_need_resume_{filter_key_base}", False):
            st.info("🔍 Showing companies where you haven't shared resume")
            filtered_companies = [comp for comp in filtered_companies if not comp.get('resume_shared', False)]
        elif st.session_state.get(f"show_apply_online_{filter_key_base}", False):
            st.info("🔍 Showing companies marked for online application")
            filtered_companies = [comp for comp in filtered_companies if comp.get('apply_online', False)]
        
        # Display filtered companies
        if len(filtered_companies) > 0:
            st.write(f"Showing **{len(filtered_companies)}** of **{len(companies)}** companies:")
            
            # Automatically detect if mobile device
            is_mobile = self.is_mobile_device()
            
            if is_mobile:
                # Mobile-friendly card layout
                st.subheader("📝 Company Cards")
                
                for i, company in enumerate(filtered_companies):
                    booth_number = company.get('booth_number', 'N/A')
                    company_name = company.get('name', 'N/A')
                    education_level = company.get('education_level', 'Unknown')
                    industry = company.get('industry', 'Not specified')
                    
                    # Create unique key suffix to avoid conflicts between Day 1 and Day 2
                    unique_key_suffix = venue_name.replace(' ', '_').replace('-', '_')
                    
                    # Card container
                    with st.container():
                        # Use custom styling for mobile cards
                        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
                        st.markdown(f"### {booth_number} - {company_name}")
                        
                        # Company info in two columns
                        info_col1, info_col2 = st.columns(2)
                        with info_col1:
                            st.write(f"**Industry:** {industry}")
                        with info_col2:
                            st.write(f"**Education:** {education_level}")
                        
                        # Action checkboxes in a more compact layout
                        st.markdown("**Actions:**")
                        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                        
                        with action_col1:
                            interested = st.checkbox(
                                "⭐ Interested", 
                                value=company.get('interested', False), 
                                key=f"mobile_interested_{booth_number}_{unique_key_suffix}_{i}"
                            )
                            if interested != company.get('interested', False):
                                self.pdf_reader.update_user_interaction(booth_number, interested=interested)
                                st.rerun()
                        
                        with action_col2:
                            visited = st.checkbox(
                                "✓ Visited", 
                                value=company.get('visited', False), 
                                key=f"mobile_visited_{booth_number}_{unique_key_suffix}_{i}"
                            )
                            if visited != company.get('visited', False):
                                self.pdf_reader.update_user_interaction(booth_number, visited=visited)
                                st.rerun()
                        
                        with action_col3:
                            resume_shared = st.checkbox(
                                "📄 Resume", 
                                value=company.get('resume_shared', False), 
                                key=f"mobile_resume_{booth_number}_{unique_key_suffix}_{i}"
                            )
                            if resume_shared != company.get('resume_shared', False):
                                self.pdf_reader.update_user_interaction(booth_number, resume_shared=resume_shared)
                                st.rerun()
                        
                        with action_col4:
                            apply_online = st.checkbox(
                                "💻 Apply Online", 
                                value=company.get('apply_online', False), 
                                key=f"mobile_apply_{booth_number}_{unique_key_suffix}_{i}"
                            )
                            if apply_online != company.get('apply_online', False):
                                self.pdf_reader.update_user_interaction(booth_number, apply_online=apply_online)
                                st.rerun()
                        
                        # Comments section - full width
                        current_comments = company.get('comments', '')
                        new_comments = st.text_input(
                            "💭 Comments",
                            value=current_comments,
                            key=f"mobile_comments_{booth_number}_{unique_key_suffix}_{i}",
                            placeholder="Add notes..."
                        )
                        if new_comments != current_comments:
                            self.pdf_reader.update_user_interaction(booth_number, comments=new_comments)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Add some spacing between cards
                        st.markdown("<br>", unsafe_allow_html=True)
            
            else:
                # Desktop table layout (existing)
                st.subheader("📝 Interactive Company Table")
                
                # Responsive table with fewer columns for better mobile experience
                col_company, col_industry, col_actions, col_comments = st.columns([3, 2, 3, 3])
                
                with col_company:
                    st.write("**Company (Booth)**")
                with col_industry:
                    st.write("**Industry**")
                with col_actions:
                    st.write("**Actions**")
                with col_comments:
                    st.write("**Comments**")
                
                st.divider()
                
                # Interactive rows for each company
                for i, company in enumerate(filtered_companies):
                    booth_number = company.get('booth_number', 'N/A')
                    company_name = company.get('name', 'N/A')
                    education_level = company.get('education_level', 'Unknown')
                    industry = company.get('industry', 'Not specified')
                    
                    # Create columns for this row
                    col_company, col_industry, col_actions, col_comments = st.columns([3, 2, 3, 3])
                    
                    with col_company:
                        # Color-code by education level
                        if education_level == 'Undergraduate':
                            st.markdown(f'<span style="background-color: #e3f2fd; padding: 2px 4px; border-radius: 3px;"><strong>{booth_number}</strong> - {company_name}</span>', unsafe_allow_html=True)
                        elif education_level == 'Postgraduate':
                            st.markdown(f'<span style="background-color: #f3e5f5; padding: 2px 4px; border-radius: 3px;"><strong>{booth_number}</strong> - {company_name}</span>', unsafe_allow_html=True)
                        elif education_level == 'Both':
                            st.markdown(f'<span style="background-color: #e8f5e8; padding: 2px 4px; border-radius: 3px;"><strong>{booth_number}</strong> - {company_name}</span>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<span style="background-color: #fff3e0; padding: 2px 4px; border-radius: 3px;"><strong>{booth_number}</strong> - {company_name}</span>', unsafe_allow_html=True)
                        
                        st.caption(f"Education: {education_level}")
                    
                    with col_industry:
                        st.write(industry)
                    
                    # Create unique key suffix to avoid conflicts between Day 1 and Day 2
                    unique_key_suffix = venue_name.replace(' ', '_').replace('-', '_')
                    
                    with col_actions:
                        # Compact action buttons in a grid
                        action_sub1, action_sub2 = st.columns(2)
                        
                        with action_sub1:
                            interested = st.checkbox(
                                "⭐", 
                                value=company.get('interested', False), 
                                key=f"interested_{booth_number}_{unique_key_suffix}_{i}",
                                help="Mark as interested"
                            )
                            if interested != company.get('interested', False):
                                self.pdf_reader.update_user_interaction(booth_number, interested=interested)
                                st.rerun()
                            
                            resume_shared = st.checkbox(
                                "📄", 
                                value=company.get('resume_shared', False), 
                                key=f"resume_{booth_number}_{unique_key_suffix}_{i}",
                                help="Resume shared"
                            )
                            if resume_shared != company.get('resume_shared', False):
                                self.pdf_reader.update_user_interaction(booth_number, resume_shared=resume_shared)
                                st.rerun()
                        
                        with action_sub2:
                            visited = st.checkbox(
                                "✓", 
                                value=company.get('visited', False), 
                                key=f"visited_{booth_number}_{unique_key_suffix}_{i}",
                                help="Mark as visited"
                            )
                            if visited != company.get('visited', False):
                                self.pdf_reader.update_user_interaction(booth_number, visited=visited)
                                st.rerun()
                            
                            apply_online = st.checkbox(
                                "💻", 
                                value=company.get('apply_online', False), 
                                key=f"apply_{booth_number}_{unique_key_suffix}_{i}",
                                help="Apply online"
                            )
                            if apply_online != company.get('apply_online', False):
                                self.pdf_reader.update_user_interaction(booth_number, apply_online=apply_online)
                                st.rerun()
                    
                    with col_comments:
                        current_comments = company.get('comments', '')
                        new_comments = st.text_input(
                            "Comments",
                            value=current_comments,
                            key=f"comments_{booth_number}_{unique_key_suffix}_{i}",
                            placeholder="Add notes...",
                            label_visibility="collapsed"
                        )
                        if new_comments != current_comments:
                            self.pdf_reader.update_user_interaction(booth_number, comments=new_comments)
                    
                    # Add a subtle divider between rows
                    if i < len(filtered_companies) - 1:
                        st.markdown("---")
            
            # Bulk actions section
            st.subheader("🔧 Bulk Actions")
            bulk_col1, bulk_col2, bulk_col3 = st.columns(3)
            
            # Create unique bulk action keys
            bulk_key_base = venue_name.replace(' ', '_').replace('-', '_')
            
            with bulk_col1:
                if st.button("Mark All as Visited", key=f"bulk_visited_{bulk_key_base}"):
                    for company in filtered_companies:
                        self.pdf_reader.update_user_interaction(company['booth_number'], visited=True)
                    st.success(f"Marked {len(filtered_companies)} companies as visited!")
                    st.rerun()
            
            with bulk_col2:
                if st.button("Clear All Visited", key=f"bulk_clear_visited_{bulk_key_base}"):
                    for company in filtered_companies:
                        self.pdf_reader.update_user_interaction(company['booth_number'], visited=False)
                    st.success(f"Cleared visited status for {len(filtered_companies)} companies!")
                    st.rerun()
            
            with bulk_col3:
                if st.button("Export to CSV", key=f"export_{bulk_key_base}"):
                    import pandas as pd
                    export_data = []
                    for company in filtered_companies:
                        export_data.append({
                            'Booth': company.get('booth_number', ''),
                            'Company': company.get('name', ''),
                            'Education Level': company.get('education_level', ''),
                            'Industry': company.get('industry', ''),
                            'Interested': company.get('interested', False),
                            'Visited': company.get('visited', False),
                            'Resume Shared': company.get('resume_shared', False),
                            'Apply Online': company.get('apply_online', False),
                            'Comments': company.get('comments', '')
                        })
                    
                    df = pd.DataFrame(export_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"career_fair_{venue_name.replace(' ', '_').lower()}.csv",
                        mime="text/csv"
                    )
        else:
            st.warning("No companies found matching the selected education level criteria.")
    
    def display_resume_match_tab(self):
        """Display the resume matching tab"""
        st.header("🎯 Resume & Preference Matcher")
        st.markdown("""
        **Find your perfect company matches!** Upload your resume and tell us about your career preferences. 
        Our AI will analyze your background and recommend the best companies for you at the career fair.
        """)
        
        # Check if OpenAI is available
        if not hasattr(self.pdf_reader, 'analyze_resume_match'):
            st.error("❌ Resume matching requires OpenAI API access. Please configure your OpenAI API key.")
            return
        
        # Automatically detect mobile device
        is_mobile_resume = self.is_mobile_device()
        
        if is_mobile_resume:
            # Mobile layout - stacked sections
            st.subheader("📄 Upload Your Resume")
            uploaded_file = st.file_uploader(
                "Choose your resume (PDF format)",
                type=['pdf'],
                help="Upload your resume in PDF format for analysis",
                key="mobile_resume_uploader"
            )
            
            # Resume preview
            if uploaded_file is not None:
                st.success(f"✅ Resume uploaded: {uploaded_file.name}")
                
                # Extract text from resume
                with st.spinner("Extracting text from resume..."):
                    resume_text = self.pdf_reader.extract_text_from_pdf(uploaded_file)
                
                if resume_text:
                    st.info(f"📝 Extracted {len(resume_text)} characters from your resume")
                    
                    # Show preview of extracted text
                    with st.expander("🔍 Preview extracted text"):
                        st.text_area(
                            "Resume content preview",
                            resume_text[:1000] + ("..." if len(resume_text) > 1000 else ""),
                            height=150,
                            disabled=True,
                            key="mobile_resume_preview"
                        )
                else:
                    st.error("❌ Could not extract text from the PDF. Please try a different file.")
                    resume_text = ""
            else:
                resume_text = ""
                
            # Career preferences section
            st.subheader("🎯 Your Career Preferences")
            user_preferences = st.text_area(
                "Tell us about your career goals and preferences",
                placeholder="""Example:
- Looking for software engineering roles
- Interested in fintech and healthcare industries  
- Prefer companies with strong mentorship programs
- Want opportunities in data science or machine learning
- Seeking positions with international exposure""",
                height=150,
                help="Be specific about industries, roles, company culture, or any other preferences",
                key="mobile_user_preferences"
            )
            
            # Education level
            education_level = st.selectbox(
                "Your education level",
                ["Undergraduate", "Postgraduate"],
                help="This helps filter companies that accept your education level",
                key="mobile_education_level"
            )
            
        else:
            # Desktop layout - two columns
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📄 Upload Your Resume")
                uploaded_file = st.file_uploader(
                    "Choose your resume (PDF format)",
                    type=['pdf'],
                    help="Upload your resume in PDF format for analysis",
                    key="desktop_resume_uploader"
                )
                
                # Resume preview
                if uploaded_file is not None:
                    st.success(f"✅ Resume uploaded: {uploaded_file.name}")
                    
                    # Extract text from resume
                    with st.spinner("Extracting text from resume..."):
                        resume_text = self.pdf_reader.extract_text_from_pdf(uploaded_file)
                    
                    if resume_text:
                        st.info(f"📝 Extracted {len(resume_text)} characters from your resume")
                        
                        # Show preview of extracted text
                        with st.expander("🔍 Preview extracted text"):
                            st.text_area(
                                "Resume content preview",
                                resume_text[:1000] + ("..." if len(resume_text) > 1000 else ""),
                                height=200,
                                disabled=True,
                                key="desktop_resume_preview"
                            )
                    else:
                        st.error("❌ Could not extract text from the PDF. Please try a different file.")
                        resume_text = ""
                else:
                    resume_text = ""
            
            with col2:
                st.subheader("🎯 Your Career Preferences")
                user_preferences = st.text_area(
                    "Tell us about your career goals and preferences",
                    placeholder="""Example:
- Looking for software engineering roles
- Interested in fintech and healthcare industries  
- Prefer companies with strong mentorship programs
- Want opportunities in data science or machine learning
- Seeking positions with international exposure""",
                    height=200,
                    help="Be specific about industries, roles, company culture, or any other preferences",
                    key="desktop_user_preferences"
                )
                
                # Education level
                education_level = st.selectbox(
                    "Your education level",
                    ["Undergraduate", "Postgraduate"],
                    help="This helps filter companies that accept your education level",
                    key="desktop_education_level"
                )
        
        # Add education level to preferences
        if education_level:
            user_preferences += f"\n\nEducation Level: {education_level}"
        
        # Analysis section
        st.divider()
        
        if st.button("🔍 Find My Best Matches", type="primary", use_container_width=True, key="find_matches_button"):
            if not resume_text and not user_preferences:
                st.warning("⚠️ Please upload a resume or enter your preferences to get matches.")
            else:
                with st.spinner("🤖 Analyzing your profile and finding the best company matches..."):
                    # Combine resume and preferences for analysis
                    analysis_input = ""
                    if resume_text:
                        analysis_input += f"RESUME:\n{resume_text}\n\n"
                    if user_preferences:
                        analysis_input += f"PREFERENCES:\n{user_preferences}"
                    
                    # If only preferences are available, make that clear
                    if not resume_text and user_preferences:
                        analysis_input = f"STUDENT PREFERENCES AND PROFILE:\n{user_preferences}"
                    
                    # Get matches from AI analysis
                    matches = self.pdf_reader.analyze_resume_match(analysis_input, user_preferences)
                
                if matches:
                    st.success(f"🎉 Found {len(matches)} great matches for you!")
                    
                    # Mobile-friendly match display
                    for i, match in enumerate(matches):
                        if is_mobile_resume:
                            # Mobile card layout for matches
                            with st.container():
                                st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
                                st.subheader(f"{i+1}. {match['name']}")
                                
                                # Company basic info
                                info_col1, info_col2 = st.columns(2)
                                with info_col1:
                                    st.write(f"**Industry:** {match['industry']}")
                                    st.write(f"**Booth:** {match['booth_number']}")
                                with info_col2:
                                    st.write(f"**Location:** {match['venue']}")
                                    
                                    # Determine which day based on venue name
                                    if "Day 2" in match['venue']:
                                        st.write("📅 **Day 2** - October 9")
                                    else:
                                        st.write("📅 **Day 1** - October 8")
                                
                                # Match score prominently displayed
                                match_pct = match.get('match_percentage', 0)
                                if match_pct >= 80:
                                    st.success(f"🎯 **Match Score: {match_pct}%** - Excellent!")
                                elif match_pct >= 60:
                                    st.info(f"🎯 **Match Score: {match_pct}%** - Good match")
                                else:
                                    st.warning(f"🎯 **Match Score: {match_pct}%** - Fair match")
                                
                                # Match explanation
                                if 'explanation' in match:
                                    with st.expander("🤔 Why it's a good match"):
                                        st.write(match['explanation'])
                                
                                # Alignment factors
                                if 'alignment_factors' in match and match['alignment_factors']:
                                    with st.expander("🔑 Key alignments"):
                                        for factor in match['alignment_factors']:
                                            st.write(f"• {factor}")
                                
                                # Action buttons for mobile
                                action_col1, action_col2 = st.columns(2)
                                unique_match_key = f"{match['booth_number']}_{match['venue'].replace(' ', '_')}"
                                
                                with action_col1:
                                    if st.button(f"⭐ Mark Interested", key=f"mobile_match_interested_{unique_match_key}", use_container_width=True):
                                        self.pdf_reader.update_user_interaction(match['booth_number'], interested=True)
                                        st.success("✅ Marked as interested!")
                                        st.rerun()
                                
                                with action_col2:
                                    if st.button(f"✓ Add to Visited", key=f"mobile_match_visited_{unique_match_key}", use_container_width=True):
                                        self.pdf_reader.update_user_interaction(match['booth_number'], visited=True)
                                        st.success("✅ Added to visited list!")
                                        st.rerun()
                                
                                # Job search links - simplified for mobile
                                with st.expander("🔍 Find Jobs at this Company"):
                                    # Generate intelligent job search links
                                    links, top_keywords = self.generate_job_search_links(
                                        match['name'], 
                                        user_preferences, 
                                        resume_text, 
                                        match_info=match
                                    )
                                    
                                    # Display links as full-width buttons for mobile
                                    st.markdown(f"**🔍 Job Search Keywords:** {', '.join(top_keywords[:5])}")
                                    
                                    st.markdown(f"[📘 LinkedIn Jobs]({links['linkedin']})")
                                    st.markdown(f"[🏢 Glassdoor]({links['glassdoor']})")
                                    st.markdown(f"[💼 Indeed]({links['indeed']})")
                                    st.markdown(f"[🌐 Company Careers]({links['company_careers']})")
                                
                                st.markdown('</div>', unsafe_allow_html=True)
                                st.markdown("<br>", unsafe_allow_html=True)
                        
                        else:
                            # Desktop layout for matches
                            with st.container():
                                # Create columns for match display
                                match_col1, match_col2, match_col3 = st.columns([3, 1, 1])
                                
                                with match_col1:
                                    st.subheader(f"{i+1}. {match['name']}")
                                    st.write(f"**Industry:** {match['industry']}")
                                    st.write(f"**Location:** {match['venue']}")
                                    
                                    # Determine which day based on venue name
                                    if "Day 2" in match['venue']:
                                        day_info = "📅 **Day 2** - October 9, 2025"
                                    else:
                                        day_info = "📅 **Day 1** - October 8, 2025"
                                    st.write(day_info)
                                    
                                    # Match explanation
                                    if 'explanation' in match:
                                        st.write(f"**Why it's a good match:** {match['explanation']}")
                                    
                                    # Alignment factors
                                    if 'alignment_factors' in match and match['alignment_factors']:
                                        st.write("**Key alignments:**")
                                        for factor in match['alignment_factors']:
                                            st.write(f"• {factor}")
                                    
                                    # Job search links
                                    st.write("**🔍 Find Jobs:**")
                                    # Generate intelligent job search links
                                    links, top_keywords = self.generate_job_search_links(
                                        match['name'], 
                                        user_preferences, 
                                        resume_text, 
                                        match_info=match
                                    )
                                    
                                    # Display links as buttons
                                    link_col1, link_col2, link_col3, link_col4 = st.columns(4)
                                    with link_col1:
                                        st.markdown(f"[LinkedIn]({links['linkedin']})", unsafe_allow_html=True)
                                    with link_col2:
                                        st.markdown(f"[Glassdoor]({links['glassdoor']})", unsafe_allow_html=True)
                                    with link_col3:
                                        st.markdown(f"[Indeed]({links['indeed']})", unsafe_allow_html=True)
                                    with link_col4:
                                        st.markdown(f"[Company Site]({links['company_careers']})", unsafe_allow_html=True)
                                
                                with match_col2:
                                    # Match percentage with color coding
                                    match_pct = match.get('match_percentage', 0)
                                    if match_pct >= 80:
                                        st.metric("Match Score", f"{match_pct}%", delta="Excellent", delta_color="normal")
                                    elif match_pct >= 60:
                                        st.metric("Match Score", f"{match_pct}%", delta="Good", delta_color="normal")
                                    else:
                                        st.metric("Match Score", f"{match_pct}%", delta="Fair", delta_color="normal")
                                    
                                    st.write(f"**Booth:** {match['booth_number']}")
                                
                                with match_col3:
                                    # Action buttons with unique keys including venue info
                                    unique_match_key = f"{match['booth_number']}_{match['venue'].replace(' ', '_')}"
                                    
                                    if st.button(f"Mark Interested", key=f"match_interested_{unique_match_key}"):
                                        self.pdf_reader.update_user_interaction(match['booth_number'], interested=True)
                                        st.success("✅ Marked as interested!")
                                        st.rerun()
                                    
                                    if st.button(f"Add to Visited", key=f"match_visited_{unique_match_key}"):
                                        self.pdf_reader.update_user_interaction(match['booth_number'], visited=True)
                                        st.success("✅ Added to visited list!")
                                        st.rerun()
                            
                            st.divider()
                    for i, match in enumerate(matches):
                        with st.container():
                            # Create columns for match display
                            match_col1, match_col2, match_col3 = st.columns([3, 1, 1])
                            
                            with match_col1:
                                st.subheader(f"{i+1}. {match['name']}")
                                st.write(f"**Industry:** {match['industry']}")
                                st.write(f"**Location:** {match['venue']}")
                                
                                # Determine which day based on venue name
                                if "Day 2" in match['venue']:
                                    day_info = "📅 **Day 2** - October 9, 2025"
                                else:
                                    day_info = "📅 **Day 1** - October 8, 2025"
                                st.write(day_info)
                                
                                # Match explanation
                                if 'explanation' in match:
                                    st.write(f"**Why it's a good match:** {match['explanation']}")
                                
                                # Alignment factors
                                if 'alignment_factors' in match and match['alignment_factors']:
                                    st.write("**Key alignments:**")
                                    for factor in match['alignment_factors']:
                                        st.write(f"• {factor}")
                                
                                # Job search links
                                st.write("**🔍 Find Jobs:**")
                                company_name_encoded = match['name'].replace(' ', '%20').replace('&', '%26')
                                
                                # Generate intelligent job search links
                                links, top_keywords = self.generate_job_search_links(
                                    match['name'], 
                                    user_preferences, 
                                    resume_text, 
                                    match_info=match
                                )
                                
                                # Display links as buttons
                                link_col1, link_col2, link_col3, link_col4 = st.columns(4)
                                with link_col1:
                                    st.markdown(f"[LinkedIn]({links['linkedin']})", unsafe_allow_html=True)
                                with link_col2:
                                    st.markdown(f"[Glassdoor]({links['glassdoor']})", unsafe_allow_html=True)
                                with link_col3:
                                    st.markdown(f"[Indeed]({links['indeed']})", unsafe_allow_html=True)
                                with link_col4:
                                    st.markdown(f"[Company Site]({links['company_careers']})", unsafe_allow_html=True)
                            
                            with match_col2:
                                # Match percentage with color coding
                                match_pct = match.get('match_percentage', 0)
                                if match_pct >= 80:
                                    st.metric("Match Score", f"{match_pct}%", delta="Excellent", delta_color="normal")
                                elif match_pct >= 60:
                                    st.metric("Match Score", f"{match_pct}%", delta="Good", delta_color="normal")
                                else:
                                    st.metric("Match Score", f"{match_pct}%", delta="Fair", delta_color="normal")
                                
                                st.write(f"**Booth:** {match['booth_number']}")
                            
                            with match_col3:
                                # Action buttons with unique keys including venue info
                                unique_match_key = f"{match['booth_number']}_{match['venue'].replace(' ', '_')}"
                                
                                if st.button(f"Mark Interested", key=f"match_interested_{unique_match_key}"):
                                    self.pdf_reader.update_user_interaction(match['booth_number'], interested=True)
                                    st.success("✅ Marked as interested!")
                                    st.rerun()
                                
                                if st.button(f"Add to Visited", key=f"match_visited_{unique_match_key}"):
                                    self.pdf_reader.update_user_interaction(match['booth_number'], visited=True)
                                    st.success("✅ Added to visited list!")
                                    st.rerun()
                        
                        st.divider()
                    
                    # Export matches option
                    if st.button("📄 Export My Matches to CSV", key="export_matches_csv"):
                        import pandas as pd
                        export_data = []
                        for match in matches:
                            export_data.append({
                                'Company': match['name'],
                                'Booth': match['booth_number'],
                                'Venue': match['venue'],
                                'Industry': match['industry'],
                                'Match Percentage': match.get('match_percentage', 0),
                                'Explanation': match.get('explanation', ''),
                                'Alignment Factors': '; '.join(match.get('alignment_factors', []))
                            })
                        
                        df = pd.DataFrame(export_data)
                        st.download_button(
                            label="📄 Download My Matches CSV",
                            data=df.to_csv(index=False),
                            file_name="my_career_fair_matches.csv",
                            mime="text/csv"
                        )
                
                else:
                    st.error("❌ Could not find matches. Please try adjusting your preferences or check your resume format.")

    def generate_job_search_links(self, company_name, user_preferences, resume_text="", match_info=None):
        """Generate targeted job search links based on company and user profile"""
        
        # Extract key skills and roles from preferences and resume
        keywords = []
        
        # Extract from preferences
        if user_preferences:
            # Look for common job-related keywords
            pref_lower = user_preferences.lower()
            job_keywords = [
                'software engineer', 'data scientist', 'machine learning', 'ai', 'artificial intelligence',
                'backend', 'frontend', 'full stack', 'devops', 'cloud', 'cybersecurity', 'security',
                'product manager', 'business analyst', 'consultant', 'finance', 'marketing',
                'sales', 'research', 'internship', 'graduate', 'entry level', 'senior',
                'python', 'java', 'javascript', 'react', 'node', 'aws', 'azure', 'docker',
                'analyst', 'developer', 'specialist', 'coordinator', 'manager', 'lead'
            ]
            
            for keyword in job_keywords:
                if keyword in pref_lower:
                    keywords.append(keyword)
        
        # Extract from resume (if available)
        if resume_text:
            resume_lower = resume_text.lower()
            # Look for technical skills and experience
            resume_keywords = [
                'python', 'java', 'javascript', 'react', 'node.js', 'machine learning',
                'data science', 'sql', 'aws', 'azure', 'docker', 'kubernetes',
                'project management', 'agile', 'scrum', 'leadership'
            ]
            
            for keyword in resume_keywords:
                if keyword in resume_lower and keyword not in keywords:
                    keywords.append(keyword)
        
        # Use education level from match info
        education_level = ""
        if match_info and 'education_level' in match_info:
            if match_info['education_level'] == 'Undergraduate':
                education_level = "intern OR graduate OR entry level"
            elif match_info['education_level'] == 'Postgraduate':
                education_level = "graduate OR senior OR experienced"
            else:  # Both
                education_level = "graduate OR intern OR entry level"
        
        # Combine company name with top keywords
        company_encoded = company_name.replace(' ', '%20').replace('&', '%26')
        top_keywords = keywords[:3]  # Use top 3 most relevant keywords
        
        # Create search query
        if top_keywords:
            keyword_query = '%20'.join(top_keywords)
            if education_level:
                search_query = f"{company_encoded}%20{keyword_query}%20({education_level.replace(' ', '%20')})"
            else:
                search_query = f"{company_encoded}%20{keyword_query}"
        else:
            if education_level:
                search_query = f"{company_encoded}%20({education_level.replace(' ', '%20')})"
            else:
                search_query = company_encoded
        
        # Generate URLs with targeted search
        links = {
            'linkedin': f"https://www.linkedin.com/jobs/search/?keywords={search_query}&location=Singapore",
            'glassdoor': f"https://www.glassdoor.com/Jobs/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword={search_query}&sc.keyword={search_query}&locT=C&locId=1880252",
            'indeed': f"https://sg.indeed.com/jobs?q={search_query}&l=Singapore",
            'jobsdb': f"https://sg.jobsdb.com/jobs?keywords={search_query}",
            'company_careers': f"https://www.google.com/search?q={company_encoded}+careers+singapore+jobs"
        }
        
        return links, top_keywords
    
    def run(self):
        """Run the Streamlit app"""
        
        # Set up mobile toggle once at the start
        self.setup_mobile_toggle()
        
        # Main title
        st.title("🎯 NUS Career Fair 2025 - Student Guide")
        st.markdown("**October 8-9, 2025** | Stephen Riady Centre & Engineering Auditorium")
        
        # Welcome message with automatic detection info
        with st.expander("ℹ️ About this App", expanded=False):
            st.markdown("""
            **AI-powered Career Fair Companion** 🎉
            
            - 🤖 **AI Resume Matching:** Upload your resume for personalized company recommendations
            - 🏢 **Interactive Company Lists:** Track visited companies, mark interests, and add notes
            - 🔍 **Smart Job Search:** Generate targeted job search links based on your profile
            - 📱 **Responsive Design:** Optimized for both mobile and desktop usage
            """)
        
        st.divider()
        
        # Sidebar info
        with st.sidebar:
            # Day 1 Section in Sidebar
            st.header("📅 Day 1 - October 8, 2025")
            st.info("**Day 1 Venues**")
            
            st.markdown("**📍 Click venue to navigate:**")
            
            # Day 1 venue navigation buttons
            if st.button("🏢 SRC Hall A (Day 1)", key="nav_src_a_day1", use_container_width=True):
                st.session_state.selected_tab = 0  # Tab 0 is now Day 1
                st.session_state.selected_venue_day1 = 0
                st.session_state.navigation_message = "🎯 Navigated to SRC Hall A (Day 1)"
                st.rerun()
            
            if st.button("🏢 SRC Hall B (Day 1)", key="nav_src_b_day1", use_container_width=True):
                st.session_state.selected_tab = 0  # Tab 0 is now Day 1
                st.session_state.selected_venue_day1 = 1
                st.session_state.navigation_message = "🎯 Navigated to SRC Hall B (Day 1)"
                st.rerun()
            
            if st.button("🏢 SRC Hall C (Day 1)", key="nav_src_c_day1", use_container_width=True):
                st.session_state.selected_tab = 0  # Tab 0 is now Day 1
                st.session_state.selected_venue_day1 = 2
                st.session_state.navigation_message = "🎯 Navigated to SRC Hall C (Day 1)"
                st.rerun()
            
            if st.button("🏛️ EA Atrium (Day 1)", key="nav_ea_day1", use_container_width=True):
                st.session_state.selected_tab = 0  # Tab 0 is now Day 1
                st.session_state.selected_venue_day1 = 3
                st.session_state.navigation_message = "🎯 Navigated to EA Atrium (Day 1)"
                st.rerun()
            
            st.divider()
            
            # Day 2 Section in Sidebar
            st.header("📅 Day 2 - October 9, 2025")
            st.info("**Day 2 Venues**")
            
            st.markdown("**📍 Click venue to navigate:**")
            
            # Day 2 venue navigation buttons
            if st.button("🏢 SRC Hall A (Day 2)", key="nav_src_a_day2", use_container_width=True):
                st.session_state.selected_tab = 1  # Tab 1 is now Day 2
                st.session_state.selected_venue_day2 = 0
                st.session_state.navigation_message = "🎯 Navigated to SRC Hall A (Day 2)"
                st.rerun()
            
            if st.button("🏢 SRC Hall B (Day 2)", key="nav_src_b_day2", use_container_width=True):
                st.session_state.selected_tab = 1  # Tab 1 is now Day 2
                st.session_state.selected_venue_day2 = 1
                st.session_state.navigation_message = "🎯 Navigated to SRC Hall B (Day 2)"
                st.rerun()
            
            if st.button("🏢 SRC Hall C (Day 2)", key="nav_src_c_day2", use_container_width=True):
                st.session_state.selected_tab = 1  # Tab 1 is now Day 2
                st.session_state.selected_venue_day2 = 2
                st.session_state.navigation_message = "🎯 Navigated to SRC Hall C (Day 2)"
                st.rerun()
            
            if st.button("🏛️ EA Atrium (Day 2)", key="nav_ea_day2", use_container_width=True):
                st.session_state.selected_tab = 1  # Tab 1 is now Day 2
                st.session_state.selected_venue_day2 = 3
                st.session_state.navigation_message = "🎯 Navigated to EA Atrium (Day 2)"
                st.rerun()
        
        # Dynamic tab ordering based on current date
        from datetime import datetime
        current_date = datetime.now().date()
        oct_8 = datetime(2025, 10, 8).date()
        oct_9 = datetime(2025, 10, 9).date()
        
        # Determine default tab based on date
        if current_date < oct_8:
            default_tab = 0  # Day 1
        elif current_date < oct_9:
            default_tab = 1  # Day 2
        else:
            default_tab = 0  # Day 1 (after both dates)
        
        # Handle session state navigation override
        if 'selected_tab' in st.session_state:
            default_tab = st.session_state.selected_tab
            # Clear the session state after using it
            del st.session_state.selected_tab
        
        # Create tabs - reordered with Resume Match as fourth tab
        tab_labels = [
            "🏢 Day 1 Venues (Oct 8)", 
            "🏢 Day 2 Venues (Oct 9)", 
            "📖 Full Guide",
            "🎯 Resume Match (WIP)"
        ]
        
        # Add active indicator to the default tab
        if default_tab == 0:
            tab_labels[0] = "🏢 Day 1 Venues (Oct 8) ⭐"
        elif default_tab == 1:
            tab_labels[1] = "🏢 Day 2 Venues (Oct 9) ⭐"
        
        tab0, tab1, tab2, tab3 = st.tabs(tab_labels)
        
        # Set the active tab based on date or navigation
        if 'active_tab_index' not in st.session_state:
            st.session_state.active_tab_index = default_tab
        
        with tab0:
            st.header("Day 1 - October 8, 2025")
            st.markdown("**Venue Maps and Layouts**")
            
            # Show navigation message if available
            if 'navigation_message' in st.session_state and st.session_state.get('selected_tab', 0) == 0:
                st.success(st.session_state.navigation_message)
                # Clear the message after showing it
                del st.session_state.navigation_message
            
            # Check if a specific venue was selected from sidebar
            if 'selected_venue_day1' in st.session_state:
                venue_index = st.session_state.selected_venue_day1
                venue_names = ["SRC Hall A", "SRC Hall B", "SRC Hall C", "EA Atrium"]
                st.info(f"📍 **Quick Navigation:** Click the **{venue_names[venue_index]}** tab below to see details")
            
            # Create tabs for each venue
            venue_tab1, venue_tab2, venue_tab3, venue_tab4 = st.tabs([
                "🏢 SRC Hall A", 
                "🏢 SRC Hall B", 
                "🏢 SRC Hall C", 
                "🏛️ EA Atrium"
            ])
            
            with venue_tab1:
                self.display_map_page(10, "SRC Hall A - Sports Hall 1 (Level 1)")
                st.divider()
                self.display_company_table("SRC Hall A")
            
            with venue_tab2:
                self.display_map_page(13, "SRC Hall B - Sports Hall 2 (Level 1)")
                st.divider()
                self.display_company_table("SRC Hall B")
            
            with venue_tab3:
                self.display_map_page(16, "SRC Hall C - Sports Hall 3 (Level 1)")
                st.divider()
                self.display_company_table("SRC Hall C")
            
            with venue_tab4:
                self.display_map_page(19, "EA Atrium Layout")
                st.divider()
                self.display_company_table("EA Atrium")
        
        with tab1:
            st.header("Day 2 - October 9, 2025")
            st.markdown("**Venue Maps and Layouts**")
            
            # Show navigation message if available
            if 'navigation_message' in st.session_state and st.session_state.get('selected_tab', 0) == 1:
                st.success(st.session_state.navigation_message)
                # Clear the message after showing it
                del st.session_state.navigation_message
            
            # Check if a specific venue was selected from sidebar
            if 'selected_venue_day2' in st.session_state:
                venue_index = st.session_state.selected_venue_day2
                venue_names = ["SRC Hall A", "SRC Hall B", "SRC Hall C", "EA Atrium"]
                st.info(f"📍 **Quick Navigation:** Click the **{venue_names[venue_index]}** tab below to see details")
            
            # Create tabs for each Day 2 venue
            venue_tab1_d2, venue_tab2_d2, venue_tab3_d2, venue_tab4_d2 = st.tabs([
                "🏢 SRC Hall A", 
                "🏢 SRC Hall B", 
                "🏢 SRC Hall C", 
                "🏛️ EA Atrium"
            ])
            
            with venue_tab1_d2:
                self.display_map_page(22, "SRC Hall A - Day 2 Layout (Sports Hall 1, Level 1)")
                st.divider()
                self.display_company_table("Day 2 - SRC Hall A")
            
            with venue_tab2_d2:
                self.display_map_page(25, "SRC Hall B - Day 2 Layout (Sports Hall 2, Level 1)")
                st.divider()
                self.display_company_table("Day 2 - SRC Hall B")
            
            with venue_tab3_d2:
                self.display_map_page(28, "SRC Hall C - Day 2 Layout (Sports Hall 3, Level 1)")
                st.divider()
                self.display_company_table("Day 2 - SRC Hall C")
            
            with venue_tab4_d2:
                self.display_map_page(31, "EA Atrium - Day 2 Layout")
                st.divider()
                self.display_company_table("Day 2 - EA Atrium")
        
        with tab2:
            st.header("📖 Complete Career Fair Guide")
            st.markdown("**Full PDF Document with all information**")
            
            # Overview section
            st.subheader("📋 Event Overview")
            st.markdown("""
            **NUS Career Fair 2025**
            - 📅 **Dates:** October 8-9, 2025
            - 📍 **Locations:** Stephen Riady Centre (SRC) & Engineering Auditorium (EA)
            - 🕒 **Time:** 10:00 AM - 5:00 PM (both days)
            - 🎓 **For:** All NUS students (Undergraduate & Postgraduate)
            """)
            
            # Quick navigation
            st.subheader("🗺️ Venue Maps & Information")
            
            # Show all venue maps
            map_col1, map_col2 = st.columns(2)
            
            with map_col1:
                st.markdown("**Day 1 Maps (October 8)**")
                self.display_map_page(10, "Day 1 - SRC Hall A")
                self.display_map_page(13, "Day 1 - SRC Hall B") 
                self.display_map_page(16, "Day 1 - SRC Hall C")
                self.display_map_page(19, "Day 1 - EA Atrium")
            
            with map_col2:
                st.markdown("**Day 2 Maps (October 9)**")
                self.display_map_page(22, "Day 2 - SRC Hall A")
                self.display_map_page(25, "Day 2 - SRC Hall B")
                self.display_map_page(28, "Day 2 - SRC Hall C") 
                self.display_map_page(31, "Day 2 - EA Atrium")
            
            # PDF page navigator
            st.subheader("📄 PDF Page Navigator")
            page_number = st.number_input(
                "Select page to view:", 
                min_value=1, 
                max_value=self.pdf_reader.total_pages if hasattr(self.pdf_reader, 'total_pages') else 50, 
                value=1,
                key="page_navigator"
            )
            
            if PYMUPDF_AVAILABLE:
                # Display page as image
                with st.spinner(f"Loading page {page_number}..."):
                    image = self.convert_pdf_page_to_image(page_number)
                    if image:
                        st.image(image, caption=f"Page {page_number}", width='stretch')
                    else:
                        st.error(f"Could not load page {page_number}")
            else:
                st.info("📄 PDF page rendering as image not available. Showing text content below.")
            
            # Display text content
            self.display_page_text(page_number)
        
        with tab3:
            st.header("🎯 Resume & Preference Matcher")
            st.info("⚠️ **Work in Progress** - This feature is currently being enhanced with advanced AI capabilities.")
            st.markdown("""
            **Coming Soon:**
            - 🤖 Enhanced AI resume analysis
            - 🎯 More accurate company matching algorithms
            - 📊 Detailed compatibility scoring system
            - 🔍 Advanced job search integration
            - 💼 Industry-specific recommendations
            - 📈 Career path suggestions
            
            **Current Status:** Basic functionality available, improvements in development.
            """)
            
            # Still show the existing functionality but with WIP notice
            with st.expander("🚧 Try Current Version (Beta)", expanded=False):
                st.warning("Note: This is a beta version with limited accuracy. Enhanced version coming soon!")
                self.display_resume_match_tab()


def main():
    """Main function to run the Streamlit app"""
    app = CareerFairApp()
    app.run()


if __name__ == "__main__":
    main()
