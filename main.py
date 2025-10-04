"""
Career Fair Buddy - Main Application (Modular Version)
A streamlined, modular version of the original streamlit_app.py
"""
import streamlit as st
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.config import Config
from src.pdf_reader import CareerFairPDFReader
from src.user_manager import UserManager
from src.ui.styles import get_custom_css
from src.ui.mobile import MobileManager


# Page configuration
st.set_page_config(
    page_title="Career Fair Buddy",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://github.com/your-repo/career-fair-buddy',
        'Report a bug': 'https://github.com/your-repo/career-fair-buddy/issues',
        'About': '# Career Fair Buddy\\nYour AI-powered career fair companion!'
    }
)


class CareerFairApp:
    """Main Career Fair Buddy application class"""
    
    def __init__(self):
        """Initialize the application"""
        self.setup_user_id()
        self.mobile_manager = MobileManager()
        self.pdf_reader = None
        
        # Apply custom CSS
        st.markdown(get_custom_css(), unsafe_allow_html=True)
        
        # Initialize PDF reader
        self.init_pdf_reader()
    
    def setup_user_id(self):
        """Set up unique user ID for multi-user support"""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = UserManager.generate_user_id()
        
        # Display user ID in sidebar
        with st.sidebar:
            st.write("### 👤 User Profile")
            st.write(f"**User ID:** `{st.session_state.user_id}`")
            st.caption("Your unique ID for this session. Data is saved automatically.")
            
            # System metrics
            self.display_system_metrics()
            
            # Export user data
            self.display_export_options()
    
    def display_system_metrics(self):
        """Display system-wide metrics in sidebar"""
        try:
            metrics = UserManager.get_system_metrics()
            
            st.write("### 📊 System Status")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Active Users", metrics['active_users_24h'])
            with col2:
                st.metric("Storage", metrics['total_storage_formatted'])
            
            # Show warnings if any
            if metrics['warnings']:
                st.warning("⚠️ Performance Impact")
                for warning in metrics['warnings']:
                    st.caption(f"• {warning}")
            else:
                st.success("✅ System Operating Normally")
                
        except Exception as e:
            st.error(f"Could not load system metrics: {e}")
    
    def display_export_options(self):
        """Display data export options in sidebar"""
        st.write("### 📥 Export Data")
        
        if st.button("Export My Data", help="Download your interaction data as CSV"):
            if self.pdf_reader:
                csv_data = self.pdf_reader.export_user_data()
                
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"career_fair_data_{st.session_state.user_id}.csv",
                    mime="text/csv"
                )
                st.success("✅ Data export ready!")
            else:
                st.error("PDF reader not initialized")
    
    def init_pdf_reader(self):
        """Initialize PDF reader with current user ID"""
        try:
            validation_issues = Config.validate_setup()
            if validation_issues:
                st.error("⚠️ Configuration Issues:")
                for issue in validation_issues:
                    st.write(f"• {issue}")
                return
            
            # Initialize with user ID
            self.pdf_reader = CareerFairPDFReader(user_id=st.session_state.user_id)
            
            # Display cache stats
            cache_stats = self.pdf_reader.get_cache_stats()
            st.sidebar.write("### 💾 Cache Status")
            st.sidebar.write(f"**Entries:** {cache_stats['total_entries']}")
            st.sidebar.write(f"**Size:** {cache_stats['file_size_formatted']}")
            
        except FileNotFoundError as e:
            st.error(f"📄 PDF file not found: {e}")
        except Exception as e:
            st.error(f"❌ Failed to initialize PDF reader: {e}")
    
    def display_venue_companies(self, venue_name: str):
        """Display companies for a specific venue"""
        if not self.pdf_reader:
            st.error("PDF reader not initialized")
            return
        
        try:
            with st.spinner(f"Loading companies for {venue_name}..."):
                companies = self.pdf_reader.get_venue_companies(venue_name)
            
            if not companies:
                st.warning(f"No companies found for {venue_name}")
                return
            
            # Get day and clean venue name for display
            day = Config.get_day_from_venue(venue_name)
            clean_venue = Config.get_clean_venue_name(venue_name)
            
            st.write(f"### 🏢 Companies in {clean_venue}")
            st.write(f"**{day}** • Found **{len(companies)}** companies")
            
            # Search and filter
            search_col, filter_col = st.columns([2, 1])
            
            with search_col:
                search_term = st.text_input(
                    "Search companies", 
                    placeholder=self.mobile_manager.get_search_placeholder(),
                    key=f"search_{venue_name}"
                )
            
            with filter_col:
                education_filter = st.selectbox(
                    "Education Level",
                    options=["All"] + Config.EDUCATION_LEVELS,
                    key=f"education_filter_{venue_name}"
                )
            
            # Filter companies
            filtered_companies = self.filter_companies(companies, search_term, education_filter)
            
            # Show filter results
            if len(filtered_companies) != len(companies):
                st.info(f"Showing {len(filtered_companies)} of {len(companies)} companies")
            
            # Display companies
            self.display_company_list(filtered_companies)
            
        except Exception as e:
            st.error(f"Error loading companies: {e}")
    
    def filter_companies(self, companies: list, search_term: str, education_filter: str = "All") -> list:
        """Filter companies based on search term and education level"""
        filtered = companies
        
        # Apply search filter
        if search_term:
            search_lower = search_term.lower()
            filtered = [
                company for company in filtered
                if (search_lower in company['name'].lower() or
                    search_lower in company['industry'].lower() or
                    search_lower in company['booth_number'].lower())
            ]
        
        # Apply education filter
        if education_filter != "All":
            filtered = [
                company for company in filtered
                if (company['education_level'] == education_filter or 
                    company['education_level'] == "Both")
            ]
        
        return filtered
    
    def display_company_list(self, companies: list):
        """Display list of companies with interaction tracking"""
        if not companies:
            st.warning("No companies found matching your criteria.")
            return
        
        # Show all companies by default, with option to paginate for large lists
        show_all = st.checkbox("Show all companies", value=True, help="Uncheck to enable pagination for large lists")
        
        if show_all or len(companies) <= 50:
            # Show all companies
            page_companies = companies
            st.info(f"Displaying all {len(companies)} companies")
        else:
            # Use pagination for very large lists
            items_per_page = self.mobile_manager.get_items_per_page()
            total_pages = (len(companies) - 1) // items_per_page + 1
            
            page = st.select_slider(
                "Page", 
                options=list(range(1, total_pages + 1)),
                value=1,
                format_func=lambda x: f"Page {x} of {total_pages}"
            )
            
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_companies = companies[start_idx:end_idx]
            st.info(f"Showing {len(page_companies)} companies (Page {page} of {total_pages})")
        
        # Display companies
        cols_config = self.mobile_manager.get_column_config()
        cols = st.columns(cols_config['company_list_cols'])
        
        for i, company in enumerate(page_companies):
            col_idx = i % len(cols)
            
            with cols[col_idx]:
                self.display_company_card(company)
    
    def display_company_card(self, company: dict):
        """Display individual company card with interactions"""
        # Create a container with consistent styling
        with st.container():
            # Company header with consistent layout
            st.markdown(f"""
            <div style="
                background: #f8f9fa;
                padding: 0.5rem;
                border-radius: 8px;
                border-left: 4px solid #007bff;
                margin-bottom: 0.5rem;
            ">
                <h4 style="margin: 0; color: #495057;">🏢 {company['name']}</h4>
                <p style="margin: 0; color: #6c757d;">📍 Booth {company['booth_number']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Company details in consistent format
            detail_col1, detail_col2 = st.columns(2)
            with detail_col1:
                st.markdown(f"**🎓 Education:** {company['education_level']}")
            with detail_col2:
                st.markdown(f"**🏭 Industry:** {company['industry']}")
            
            # Interaction checkboxes in consistent grid
            st.markdown("**Track Your Interactions:**")
            
            booth_number = company['booth_number']
            
            # First row of interactions
            inter_col1, inter_col2 = st.columns(2)
            
            with inter_col1:
                visited = st.checkbox(
                    "✅ Visited", 
                    value=company['visited'],
                    key=f"visited_{booth_number}"
                )
                
                resume_shared = st.checkbox(
                    "📄 Resume Shared", 
                    value=company['resume_shared'],
                    key=f"resume_{booth_number}"
                )
            
            with inter_col2:
                interested = st.checkbox(
                    "⭐ Interested", 
                    value=company['interested'],
                    key=f"interested_{booth_number}"
                )
                
                apply_online = st.checkbox(
                    "🌐 Applied Online", 
                    value=company['apply_online'],
                    key=f"apply_{booth_number}"
                )
            
            # Comments section with consistent height
            comments = st.text_area(
                "💭 Notes & Comments",
                value=company['comments'],
                key=f"comments_{booth_number}",
                height=80,
                placeholder="Add your notes about this company..."
            )
            
            # Update data if changed
            if (visited != company['visited'] or 
                interested != company['interested'] or
                resume_shared != company['resume_shared'] or
                apply_online != company['apply_online'] or
                comments != company['comments']):
                
                self.pdf_reader.update_user_interaction(
                    booth_number,
                    visited=visited,
                    interested=interested,
                    resume_shared=resume_shared,
                    apply_online=apply_online,
                    comments=comments
                )
                # Show a subtle success indicator
                st.success("✅ Saved!", icon="💾")
        
        # Consistent spacing between cards
        st.markdown("---")
    
    def display_resume_matcher(self):
        """Display resume matching functionality"""
        st.write("### 🎯 Resume Matcher")
        st.write("Upload your resume to find the best matching companies!")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose your resume PDF",
            type="pdf",
            help="Upload your resume in PDF format for analysis"
        )
        
        if uploaded_file:
            # Extract text from PDF
            with st.spinner("Extracting text from resume..."):
                resume_text = self.pdf_reader.extract_text_from_pdf(uploaded_file)
            
            if not resume_text:
                st.error("Could not extract text from PDF. Please try a different file.")
                return
            
            st.success(f"✅ Extracted {len(resume_text)} characters from resume")
            
            # User preferences
            preferences = st.text_area(
                "Additional Preferences (Optional)",
                placeholder="e.g., I'm interested in technology companies, prefer startups, looking for internships...",
                height=100
            )
            
            # Analyze matches
            if st.button("🔍 Find Matching Companies"):
                with st.spinner("Analyzing resume and finding matches..."):
                    matches = self.pdf_reader.analyze_resume_match(resume_text, preferences)
                
                if matches:
                    st.write(f"### 🎯 Top {len(matches)} Matches")
                    
                    # Group matches by day
                    day1_matches = [m for m in matches if "Day 2" not in m.get('venue', '')]
                    day2_matches = [m for m in matches if "Day 2" in m.get('venue', '')]
                    
                    # Display day summary
                    if day1_matches and day2_matches:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"📅 **Day 1**: {len(day1_matches)} matches")
                        with col2:
                            st.info(f"📅 **Day 2**: {len(day2_matches)} matches")
                    
                    for i, match in enumerate(matches, 1):
                        # Determine day for display
                        day = Config.get_day_from_venue(match.get('venue', ''))
                        clean_venue = Config.get_clean_venue_name(match.get('venue', 'Unknown'))
                        
                        with st.expander(f"{i}. {match['name']} - {match.get('match_percentage', 0)}% match ({day})"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**Company:** {match['name']}")
                                st.write(f"**Booth:** {match['booth_number']}")
                                st.write(f"**Industry:** {match['industry']}")
                                st.write(f"**Education:** {match['education_level']}")
                                st.write(f"**Day:** {day}")
                                st.write(f"**Venue:** {clean_venue}")
                                
                                if match.get('explanation'):
                                    st.write(f"**Why it matches:** {match['explanation']}")
                            
                            with col2:
                                st.metric("Match %", f"{match.get('match_percentage', 0)}%")
                                
                                if match.get('alignment_factors'):
                                    st.write("**Key Factors:**")
                                    for factor in match['alignment_factors']:
                                        st.write(f"• {factor}")
                else:
                    st.warning("No suitable matches found. Try adjusting your preferences or upload a different resume.")
    
    def convert_pdf_page_to_image(self, page_number: int):
        """Convert PDF page to image for display"""
        try:
            import fitz  # PyMuPDF
            import io
            from PIL import Image
            
            # Open PDF and get page
            doc = fitz.open(str(Config.PDF_FILE_PATH))
            page = doc[page_number - 1]  # Convert to 0-indexed
            
            # Use appropriate resolution for display
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for good quality
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PNG bytes
            img_data = pix.tobytes("png")
            doc.close()
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))
            
            # Optimize size for web display
            max_width = 800
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            st.error(f"Error converting PDF page {page_number}: {e}")
            return None
    
    def display_venue_map(self, venue_name: str, day: str, expanded: bool = False):
        """Display the map for a specific venue and day"""
        # Map page mappings - these are the pages with the actual venue layouts
        venue_map_pages = {
            # Day 1 maps
            'SRC Hall A': 10,
            'SRC Hall B': 13, 
            'SRC Hall C': 16,
            'EA Atrium': 19,
            # Day 2 maps
            'SRC Hall A Day 2': 22,
            'SRC Hall B Day 2': 25,
            'SRC Hall C Day 2': 28,
            'EA Atrium Day 2': 31
        }
        
        clean_venue = Config.get_clean_venue_name(venue_name)
        full_venue_key = venue_name if "Day 2" in venue_name else clean_venue
        
        map_page = venue_map_pages.get(full_venue_key)
        
        if map_page:
            # Add collapse/expand hint to the expander title
            expand_hint = " (click to collapse)" if expanded else " (click to expand)"
            
            with st.expander(f"🗺️ {clean_venue} Layout Map ({day}){expand_hint}", expanded=expanded):
                st.write(f"Venue layout for {clean_venue} on {day}")
                
                # Convert and display the map
                image = self.convert_pdf_page_to_image(map_page)
                if image:
                    st.image(image, 
                            caption=f"{clean_venue} - {day} Layout", 
                            use_container_width=True)
                else:
                    st.error(f"Could not load map for {clean_venue}")
        else:
            st.warning(f"Map not available for {venue_name}")

    def run(self):
        """Main application runner"""
        # App header
        st.title("🎯 Career Fair Buddy")
        st.markdown("Your AI-powered career fair companion")
        
        # Mobile settings
        self.mobile_manager.setup_mobile_toggle()
        
        if not self.pdf_reader:
            st.error("Please check configuration and try refreshing the page.")
            return
        
        # Main navigation
        tab1, tab2, tab3 = st.tabs(["🏢 Companies", "🎯 Resume Matcher", "🗺️ Maps"])
        
        with tab1:
            # Day and venue selection with visual enhancement
            st.write("### 🗓️ Select Event Day & Venue")
            
            # Create day selection with visual indicators
            day_col1, day_col2, day_col3 = st.columns([1, 2, 1])
            
            with day_col2:
                selected_day = st.selectbox(
                    "Event Day",
                    options=["Day 1", "Day 2"],
                    help="Choose which day of the career fair",
                    format_func=lambda x: f"📅 {x} - {'Oct 8, 2025' if x == 'Day 1' else 'Oct 9, 2025'}"
                )
            
            # Venue selection based on day
            venue_col1, venue_col2, venue_col3 = st.columns([0.5, 2, 0.5])
            
            with venue_col2:
                # Get venues for selected day
                day_venues = Config.get_venues_for_day(selected_day)
                venue_options = list(day_venues.keys())
                
                selected_venue = st.selectbox(
                    f"Venue for {selected_day}",
                    venue_options,
                    help=f"Choose a venue for {selected_day}",
                    format_func=lambda x: f"🏢 {x}"
                )
            
            if selected_venue and selected_day:
                # Create full venue name for backend
                full_venue_name = Config.get_full_venue_name(selected_venue, selected_day)
                
                # Display venue info with enhanced styling
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 1rem;
                    border-radius: 10px;
                    border-left: 4px solid #007bff;
                    margin: 1rem 0;
                ">
                    <h4 style="margin: 0; color: #495057;">
                        📍 {selected_day} - {selected_venue}
                    </h4>
                    <p style="margin: 0.5rem 0 0 0; color: #6c757d;">
                        Click on companies below to track your interactions
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Display venue map first (open by default)
                self.display_venue_map(full_venue_name, selected_day, expanded=True)
                
                # Then display companies
                self.display_venue_companies(full_venue_name)
        
        with tab2:
            self.display_resume_matcher()
        
        with tab3:
            st.write("### 🗺️ Venue Maps")
            st.write("Select a day and venue to view the layout map")
            
            # Day selection for maps
            map_day_col1, map_day_col2, map_day_col3 = st.columns([1, 2, 1])
            
            with map_day_col2:
                map_selected_day = st.selectbox(
                    "Day for Map",
                    options=["Day 1", "Day 2"],
                    help="Choose which day's venue maps to view",
                    format_func=lambda x: f"📅 {x} - {'Oct 8, 2025' if x == 'Day 1' else 'Oct 9, 2025'}",
                    key="map_day_selector"
                )
            
            # Show all venues for selected day in a grid
            day_venues = Config.get_venues_for_day(map_selected_day)
            
            if day_venues:
                st.write(f"### 📅 {map_selected_day} Venue Layouts")
                
                # Create a 2x2 grid for venue maps
                venue_names = list(day_venues.keys())
                
                # Display venues in pairs
                for i in range(0, len(venue_names), 2):
                    col1, col2 = st.columns(2)
                    
                    # First venue
                    if i < len(venue_names):
                        venue1 = venue_names[i]
                        full_venue1 = Config.get_full_venue_name(venue1, map_selected_day)
                        
                        with col1:
                            st.write(f"#### 🏢 {venue1}")
                            self.display_venue_map(full_venue1, map_selected_day, expanded=True)
                    
                    # Second venue (if exists)
                    if i + 1 < len(venue_names):
                        venue2 = venue_names[i + 1]
                        full_venue2 = Config.get_full_venue_name(venue2, map_selected_day)
                        
                        with col2:
                            st.write(f"#### 🏢 {venue2}")
                            self.display_venue_map(full_venue2, map_selected_day, expanded=True)
            else:
                st.error(f"No venues found for {map_selected_day}")


def main():
    """Main entry point"""
    try:
        app = CareerFairApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.write("Please refresh the page and try again.")


if __name__ == "__main__":
    main()
