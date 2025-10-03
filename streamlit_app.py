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
                
                # Create unique key suffix to avoid conflicts between Day 1 and Day 2
                unique_key_suffix = venue_name.replace(' ', '_').replace('-', '_')
                
                with col_interested:
                    interested = st.checkbox(
                        "⭐", 
                        value=company.get('interested', False), 
                        key=f"interested_{booth_number}_{unique_key_suffix}_{i}"
                    )
                    # Auto-save when checkbox changes
                    if interested != company.get('interested', False):
                        self.pdf_reader.update_user_interaction(booth_number, interested=interested)
                        st.rerun()
                
                with col_visited:
                    visited = st.checkbox(
                        "✓", 
                        value=company.get('visited', False), 
                        key=f"visited_{booth_number}_{unique_key_suffix}_{i}"
                    )
                    # Auto-save when checkbox changes
                    if visited != company.get('visited', False):
                        self.pdf_reader.update_user_interaction(booth_number, visited=visited)
                        st.rerun()
                
                with col_resume:
                    resume_shared = st.checkbox(
                        "📄", 
                        value=company.get('resume_shared', False), 
                        key=f"resume_{booth_number}_{unique_key_suffix}_{i}"
                    )
                    # Auto-save when checkbox changes
                    if resume_shared != company.get('resume_shared', False):
                        self.pdf_reader.update_user_interaction(booth_number, resume_shared=resume_shared)
                        st.rerun()
                
                with col_apply:
                    apply_online = st.checkbox(
                        "💻", 
                        value=company.get('apply_online', False), 
                        key=f"apply_{booth_number}_{unique_key_suffix}_{i}"
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
                        key=f"comments_{booth_number}_{unique_key_suffix}_{i}",
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
        
        # Create two columns for layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📄 Upload Your Resume")
            uploaded_file = st.file_uploader(
                "Choose your resume (PDF format)",
                type=['pdf'],
                help="Upload your resume in PDF format for analysis"
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
                            disabled=True
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
                help="Be specific about industries, roles, company culture, or any other preferences"
            )
            
            # Education level
            education_level = st.selectbox(
                "Your education level",
                ["Undergraduate", "Postgraduate"],
                help="This helps filter companies that accept your education level"
            )
            
            # Add education level to preferences
            if education_level:
                user_preferences += f"\n\nEducation Level: {education_level}"
        
        # Analysis section
        st.divider()
        
        if st.button("🔍 Find My Best Matches", type="primary", use_container_width=True):
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
                    
                    # Display matches
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
                    if st.button("📄 Export My Matches to CSV"):
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
            """)
        
        # Create tabs - Resume Match as the landing tab
        tab0, tab1, tab2, tab3 = st.tabs(["� Resume Match", "�🏢 Day 1 Venues (Oct 8)", "🏢 Day 2 Venues (Oct 9)", "📖 Full Guide"])
        
        with tab0:
            self.display_resume_match_tab()
        
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
