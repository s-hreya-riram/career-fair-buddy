"""
Mobile device detection and management
Handles mobile-specific UI adaptations
"""
import streamlit as st


class MobileManager:
    """Manages mobile device detection and UI adaptations"""
    
    def __init__(self):
        self.is_mobile = self._detect_mobile()
    
    def _detect_mobile(self) -> bool:
        """Detect if user is on mobile device"""
        # Check session state first
        if 'is_mobile' in st.session_state:
            return st.session_state.is_mobile
        
        # Auto-detect based on user agent (limited in Streamlit)
        try:
            # This is a basic detection - in practice, Streamlit doesn't have full user agent access
            # We'll use the manual toggle instead
            return self._auto_detect_mobile()
        except:
            return False
    
    def _auto_detect_mobile(self) -> bool:
        """Auto-detect mobile device (limited in Streamlit)"""
        # Streamlit doesn't provide direct access to user agent
        # This is a placeholder for potential future enhancement
        return False
    
    def setup_mobile_toggle(self):
        """Set up mobile view toggle in sidebar"""
        with st.sidebar:
            st.write("### 📱 Display Settings")
            
            # Mobile toggle
            mobile_mode = st.checkbox(
                "Mobile View", 
                value=st.session_state.get('is_mobile', False),
                help="Optimize layout for mobile devices"
            )
            
            # Store in session state
            st.session_state.is_mobile = mobile_mode
            self.is_mobile = mobile_mode
            
            if mobile_mode:
                st.info("📱 Mobile optimized view enabled")
            else:
                st.info("🖥️ Desktop view enabled")
    
    def get_column_config(self):
        """Get column configuration based on device type"""
        if self.is_mobile:
            return {
                'company_list_cols': [1],  # Single column on mobile
                'filter_cols': [1],       # Single column for filters
                'map_cols': [1],          # Single column for maps
                'details_cols': [1]       # Single column for details
            }
        else:
            return {
                'company_list_cols': [1, 1],    # Equal columns for desktop
                'filter_cols': [1, 1, 1],       # Three columns for filters
                'map_cols': [1, 1],             # Two columns for maps
                'details_cols': [1, 1]          # Equal columns for details
            }
    
    def get_items_per_page(self) -> int:
        """Get number of items to display per page based on device"""
        if self.is_mobile:
            return 10  # Fewer items on mobile for better performance
        else:
            return 20  # More items on desktop
    
    def get_image_size(self) -> tuple:
        """Get optimal image size for device"""
        if self.is_mobile:
            return (350, 250)  # Smaller images for mobile
        else:
            return (600, 400)  # Larger images for desktop
    
    def should_use_expander(self) -> bool:
        """Determine if content should be in expanders"""
        return self.is_mobile  # Use expanders on mobile to save space
    
    def get_button_style(self) -> dict:
        """Get button styling for device"""
        if self.is_mobile:
            return {
                'use_container_width': True,
                'type': 'primary'
            }
        else:
            return {
                'use_container_width': False,
                'type': 'secondary'
            }
    
    def get_map_height(self) -> int:
        """Get optimal map height for device"""
        if self.is_mobile:
            return 300  # Shorter maps on mobile
        else:
            return 500  # Taller maps on desktop
    
    def get_table_config(self) -> dict:
        """Get table configuration for device"""
        if self.is_mobile:
            return {
                'hide_index': True,
                'use_container_width': True,
                'height': 400
            }
        else:
            return {
                'hide_index': True,
                'use_container_width': True,
                'height': 600
            }
    
    def format_company_card(self, company: dict) -> str:
        """Format company card based on device"""
        if self.is_mobile:
            # Compact mobile format
            return f"""
            <div class="company-card">
                <div class="booth-number">{company['booth_number']}</div>
                <div class="company-name">{company['name']}</div>
                <div class="education-badge education-{company['education_level'].lower()}">{company['education_level']}</div>
                <div class="industry-tag">{company['industry']}</div>
            </div>
            """
        else:
            # Expanded desktop format
            return f"""
            <div class="company-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="booth-number">{company['booth_number']}</div>
                    <div class="education-badge education-{company['education_level'].lower()}">{company['education_level']}</div>
                </div>
                <div class="company-name">{company['name']}</div>
                <div class="industry-tag">{company['industry']}</div>
            </div>
            """
    
    def get_search_placeholder(self) -> str:
        """Get search placeholder text for device"""
        if self.is_mobile:
            return "Search companies..."
        else:
            return "Search by company name, industry, or booth number..."
    
    def get_sidebar_width(self) -> int:
        """Get sidebar width for device"""
        if self.is_mobile:
            return 280  # Narrower sidebar on mobile
        else:
            return 350  # Wider sidebar on desktop
