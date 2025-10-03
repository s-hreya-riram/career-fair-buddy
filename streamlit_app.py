import streamlit as st
import sys
import os
from pathlib import Path
from PIL import Image
import tempfile
import io

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
        
        # Get unique education levels from companies
        available_levels = list(set([company.get('education_level', 'Unknown') for company in companies]))
        available_levels.sort()
        
        # Add "All" option
        filter_options = ["All"] + available_levels
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_levels = st.multiselect(
                "Select education levels:",
                options=filter_options,
                default=["All"],
                help="Filter companies based on whether they're open to undergraduates, postgraduates, or both",
                key=f"education_filter_{venue_name.replace(' ', '_')}"
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
                key=f"industry_filter_{venue_name.replace(' ', '_')}"
            )
        
        # Filter companies based on selection
        filtered_companies = companies
        
        if "All" not in selected_levels and selected_levels:
            filtered_companies = [
                company for company in filtered_companies 
                if company.get('education_level', 'Unknown') in selected_levels
            ]
        
        if "All" not in selected_industries and selected_industries:
            filtered_companies = [
                company for company in filtered_companies 
                if company.get('industry', 'Not specified') in selected_industries
            ]
        
        # Quick action filters
        st.subheader("🎯 Quick Action Filters")
        filter_cols = st.columns(5)
        
        with filter_cols[0]:
            if st.button("Show Interested", key=f"filter_interested_{venue_name}"):
                st.session_state[f"show_interested_{venue_name}"] = True
                st.rerun()
        
        with filter_cols[1]:
            if st.button("Show Unvisited", key=f"filter_unvisited_{venue_name}"):
                st.session_state[f"show_unvisited_{venue_name}"] = True
                st.rerun()
        
        with filter_cols[2]:
            if st.button("Show Need Resume", key=f"filter_need_resume_{venue_name}"):
                st.session_state[f"show_need_resume_{venue_name}"] = True
                st.rerun()
        
        with filter_cols[3]:
            if st.button("Show Apply Online", key=f"filter_apply_online_{venue_name}"):
                st.session_state[f"show_apply_online_{venue_name}"] = True
                st.rerun()
        
        with filter_cols[4]:
            if st.button("Show All", key=f"filter_all_{venue_name}"):
                # Clear all filter states
                for key in [f"show_interested_{venue_name}", f"show_unvisited_{venue_name}", f"show_need_resume_{venue_name}", f"show_apply_online_{venue_name}"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        # Apply quick filters
        if st.session_state.get(f"show_interested_{venue_name}", False):
            st.info("🔍 Showing only companies marked as interested")
            filtered_companies = [comp for comp in filtered_companies if comp.get('interested', False)]
        elif st.session_state.get(f"show_unvisited_{venue_name}", False):
            st.info("🔍 Showing only unvisited companies")
            filtered_companies = [comp for comp in filtered_companies if not comp.get('visited', False)]
        elif st.session_state.get(f"show_need_resume_{venue_name}", False):
            st.info("🔍 Showing companies where you haven't shared resume")
            filtered_companies = [comp for comp in filtered_companies if not comp.get('resume_shared', False)]
        elif st.session_state.get(f"show_apply_online_{venue_name}", False):
            st.info("🔍 Showing companies marked for online application")
            filtered_companies = [comp for comp in filtered_companies if comp.get('apply_online', False)]
        
        # Display filtered companies
        if len(filtered_companies) > 0:
            st.write(f"Showing **{len(filtered_companies)}** of **{len(companies)}** companies:")
            
            # Interactive table approach - display each company as a row with interactive elements
            st.subheader("📝 Interactive Company Table")
            
            # Table header
            col_booth, col_company, col_education, col_industry, col_interested, col_visited, col_resume, col_apply, col_comments = st.columns([1, 3, 2, 2, 1, 1, 1, 1, 3])
            
            with col_booth:
                st.write("**Booth**")
            with col_company:
                st.write("**Company**")
            with col_education:
                st.write("**Education**")
            with col_industry:
                st.write("**Industry**")
            with col_interested:
                st.write("**Interested**")
            with col_visited:
                st.write("**Visited**")
            with col_resume:
                st.write("**Resume**")
            with col_apply:
                st.write("**Apply Online**")
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
                col_booth, col_company, col_education, col_industry, col_interested, col_visited, col_resume, col_apply, col_comments = st.columns([1, 3, 2, 2, 1, 1, 1, 1, 3])
                
                with col_booth:
                    st.write(booth_number)
                
                with col_company:
                    # Color-code by education level
                    if education_level == 'Undergraduate':
                        st.markdown(f'<span style="background-color: #e3f2fd; padding: 2px 4px; border-radius: 3px;">{company_name}</span>', unsafe_allow_html=True)
                    elif education_level == 'Postgraduate':
                        st.markdown(f'<span style="background-color: #f3e5f5; padding: 2px 4px; border-radius: 3px;">{company_name}</span>', unsafe_allow_html=True)
                    elif education_level == 'Both':
                        st.markdown(f'<span style="background-color: #e8f5e8; padding: 2px 4px; border-radius: 3px;">{company_name}</span>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<span style="background-color: #fff3e0; padding: 2px 4px; border-radius: 3px;">{company_name}</span>', unsafe_allow_html=True)
                
                with col_education:
                    st.write(education_level)
                
                with col_industry:
                    st.write(industry)
                
                with col_interested:
                    interested = st.checkbox(
                        "⭐", 
                        value=company.get('interested', False), 
                        key=f"interested_{booth_number}_{venue_name}"
                    )
                    # Auto-save when checkbox changes
                    if interested != company.get('interested', False):
                        self.pdf_reader.update_user_interaction(booth_number, interested=interested)
                        st.rerun()
                
                with col_visited:
                    visited = st.checkbox(
                        "✓", 
                        value=company.get('visited', False), 
                        key=f"visited_{booth_number}_{venue_name}"
                    )
                    # Auto-save when checkbox changes
                    if visited != company.get('visited', False):
                        self.pdf_reader.update_user_interaction(booth_number, visited=visited)
                        st.rerun()
                
                with col_resume:
                    resume_shared = st.checkbox(
                        "📄", 
                        value=company.get('resume_shared', False), 
                        key=f"resume_{booth_number}_{venue_name}"
                    )
                    # Auto-save when checkbox changes
                    if resume_shared != company.get('resume_shared', False):
                        self.pdf_reader.update_user_interaction(booth_number, resume_shared=resume_shared)
                        st.rerun()
                
                with col_apply:
                    apply_online = st.checkbox(
                        "💻", 
                        value=company.get('apply_online', False), 
                        key=f"apply_{booth_number}_{venue_name}"
                    )
                    # Auto-save when checkbox changes
                    if apply_online != company.get('apply_online', False):
                        self.pdf_reader.update_user_interaction(booth_number, apply_online=apply_online)
                        st.rerun()
                
                with col_comments:
                    current_comments = company.get('comments', '')
                    new_comments = st.text_input(
                        "Comments",
                        value=current_comments,
                        key=f"comments_{booth_number}_{venue_name}",
                        placeholder="Add notes...",
                        label_visibility="collapsed"
                    )
                    # Auto-save when comments change and user moves focus
                    if new_comments != current_comments:
                        self.pdf_reader.update_user_interaction(booth_number, comments=new_comments)
                        # Note: We don't auto-rerun for comments to avoid losing focus while typing
                
                # Add a subtle divider between rows
                if i < len(filtered_companies) - 1:
                    st.markdown("---")
            
            # Bulk actions section
            st.subheader("🔧 Bulk Actions")
            bulk_col1, bulk_col2, bulk_col3 = st.columns(3)
            
            with bulk_col1:
                if st.button("Mark All as Visited", key=f"bulk_visited_{venue_name}"):
                    for company in filtered_companies:
                        self.pdf_reader.update_user_interaction(company['booth_number'], visited=True)
                    st.success(f"Marked {len(filtered_companies)} companies as visited!")
                    st.rerun()
            
            with bulk_col2:
                if st.button("Clear All Visited", key=f"bulk_clear_visited_{venue_name}"):
                    for company in filtered_companies:
                        self.pdf_reader.update_user_interaction(company['booth_number'], visited=False)
                    st.success(f"Cleared visited status for {len(filtered_companies)} companies!")
                    st.rerun()
            
            with bulk_col3:
                if st.button("Export to CSV", key=f"export_{venue_name}"):
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
    
    def run(self):
        """Run the Streamlit app"""
        # Page configuration
        st.set_page_config(
            page_title="NUS Career Fair 2025 Guide",
            page_icon="🎯",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Main title
        st.title("🎯 NUS Career Fair 2025 - Student Guide")
        st.markdown("**October 8-9, 2025** | Stephen Riady Centre & Engineering Auditorium")
        
        # Sidebar info
        with st.sidebar:
            st.header("📋 Quick Info")
            st.info(f"""
            **PDF Info:**
            - Total Pages: {self.pdf_reader.total_pages}
            - File: {Path(self.pdf_path).name}
            """)
            
            # OpenAI Cache Management
            if hasattr(self.pdf_reader, 'get_cache_stats'):
                st.header("🔄 OpenAI Cache")
                cache_stats = self.pdf_reader.get_cache_stats()
                st.info(f"""
                **Cache Statistics:**
                - Cached Results: {cache_stats['total_entries']}
                - Cache File: {'✅' if cache_stats['cache_file_exists'] else '❌'}
                """)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Clear Cache", help="Clear all cached OpenAI vision analysis results"):
                        self.pdf_reader.clear_cache()
                        st.success("Cache cleared!")
                        st.rerun()
                
                with col2:
                    if st.button("🔄 Preload All", help="Preload cache for all venues (may take time and cost)"):
                        with st.spinner("Preloading cache..."):
                            venues = ['SRC Hall A', 'SRC Hall B', 'SRC Hall C', 'EA Atrium',
                                     'SRC Hall A Day 2', 'SRC Hall B Day 2', 'SRC Hall C Day 2', 'EA Atrium Day 2']
                            total_hits = 0
                            total_calls = 0
                            
                            for venue in venues:
                                result = self.pdf_reader.preload_cache_for_venue(venue)
                                total_hits += result['cache_hits']
                                total_calls += result['api_calls']
                            
                            st.success(f"Preloading complete! {total_hits} cache hits, {total_calls} new API calls")
                            st.rerun()
            
            if not PYMUPDF_AVAILABLE:
                st.warning("⚠️ Image rendering disabled")
                st.info("PyMuPDF not available - install with: pip install PyMuPDF")

            st.divider()
            
            # Day 1 Section in Sidebar
            st.header("📅 Day 1 - October 8, 2025")
            st.info("**Day 1 Venues & Map Pages**")
            
            st.markdown("""
            **📍 Venue Locations:**
            - 🏢 **SRC Hall A** (Sports Hall 1, Level 1) - Page 10
            - 🏢 **SRC Hall B** (Sports Hall 2, Level 1) - Page 13  
            - 🏢 **SRC Hall C** (Sports Hall 3, Level 1) - Page 16
            - 🏛️ **EA Atrium** - Page 19
            
            **📋 Company Listings:**
            - SRC Hall A: Pages 11-12
            - SRC Hall B: Pages 14-15
            - SRC Hall C: Pages 17-18
            - EA Atrium: Pages 20-21
            """)
            
            st.divider()
            
            # Day 2 Section in Sidebar
            st.header("📅 Day 2 - October 9, 2025")
            st.info("**Day 2 Venues & Map Pages**")
            
            st.markdown("""
            **📍 Venue Locations:**
            - 🏢 **SRC Hall A** (Sports Hall 1, Level 1) - Page 22
            - 🏢 **SRC Hall B** (Sports Hall 2, Level 1) - Page 25
            - 🏢 **SRC Hall C** (Sports Hall 3, Level 1) - Page 28
            - 🏛️ **EA Atrium** - Page 31
            
            **📋 Company Listings:**
            - SRC Hall A: Pages 23-24
            - SRC Hall B: Pages 26-27
            - SRC Hall C: Pages 29-30
            - EA Atrium: Pages 32-34
            
            **✅ Status:** Day 2 content available (Pages 22-34)
            """)        # Create tabs for Day 1 venues and Full Guide
        tab1, tab2, tab3 = st.tabs(["🏢 Day 1 Venues (Oct 8)", "🏢 Day 2 Venues (Oct 9)", "📖 Full Guide"])
        
        with tab1:
            st.header("Day 1 - October 8, 2025")
            st.markdown("**Venue Maps and Layouts**")
            
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
        
        with tab2:
            st.header("Day 2 - October 9, 2025")
            st.markdown("**Venue Maps and Layouts**")
            
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
                self.display_company_table("SRC Hall A Day 2")
            
            with venue_tab2_d2:
                self.display_map_page(25, "SRC Hall B - Day 2 Layout (Sports Hall 2, Level 1)")
                st.divider()
                self.display_company_table("SRC Hall B Day 2")
            
            with venue_tab3_d2:
                self.display_map_page(28, "SRC Hall C - Day 2 Layout (Sports Hall 3, Level 1)")
                st.divider()
                self.display_company_table("SRC Hall C Day 2")
            
            with venue_tab4_d2:
                self.display_map_page(31, "EA Atrium - Day 2 Layout")
                st.divider()
                self.display_company_table("EA Atrium Day 2")
        
        with tab3:
            st.header("📖 Full PDF Guide Explorer")
            
            # Page selector
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.subheader("Page Navigator")
                page_number = st.number_input(
                    "Select page to view:", 
                    min_value=1, 
                    max_value=self.pdf_reader.total_pages, 
                    value=1,
                    key="page_navigator"
                )
            
            with col2:
                st.subheader(f"Page {page_number}")
                
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


def main():
    """Main function to run the Streamlit app"""
    app = CareerFairApp()
    app.run()


if __name__ == "__main__":
    main()
