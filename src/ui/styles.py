"""
CSS styles for Career Fair Buddy Streamlit app
Provides responsive design and mobile optimization
"""


def get_custom_css() -> str:
    """Get custom CSS for the Streamlit app"""
    return """
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
        
        .booth-number {
            font-weight: bold;
            color: #ff6b6b;
            font-size: 1.1em;
        }
        
        .company-name {
            font-size: 1.2em;
            font-weight: 600;
            margin: 0.5rem 0;
            color: #2c3e50;
        }
        
        .education-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
            margin-right: 0.5rem;
        }
        
        .education-undergraduate {
            background-color: #e8f5e8;
            color: #2d5a2d;
        }
        
        .education-postgraduate {
            background-color: #fff3cd;
            color: #856404;
        }
        
        .education-both {
            background-color: #d4edda;
            color: #155724;
        }
        
        .industry-tag {
            display: inline-block;
            padding: 0.2rem 0.4rem;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            font-size: 0.75em;
            color: #495057;
            margin-bottom: 0.5rem;
        }
        
        .interaction-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .interaction-button {
            flex: 1;
            min-width: 80px;
            padding: 0.3rem 0.6rem;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            background-color: white;
            font-size: 0.8em;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .interaction-button.active {
            background-color: #007bff;
            color: white;
            border-color: #007bff;
        }
        
        .interaction-button:hover {
            background-color: #f8f9fa;
            border-color: #adb5bd;
        }
        
        .interaction-button.active:hover {
            background-color: #0056b3;
        }
        
        .match-percentage {
            font-size: 1.5em;
            font-weight: bold;
            color: #28a745;
            text-align: center;
        }
        
        .match-explanation {
            font-style: italic;
            color: #6c757d;
            margin: 0.5rem 0;
        }
        
        .alignment-factors {
            margin-top: 0.5rem;
        }
        
        .alignment-factor {
            display: inline-block;
            padding: 0.2rem 0.4rem;
            background-color: #e9ecef;
            border-radius: 4px;
            font-size: 0.75em;
            margin-right: 0.3rem;
            margin-bottom: 0.3rem;
        }
    }
    
    /* Desktop styles */
    @media (min-width: 769px) {
        .company-card {
            margin-bottom: 1.5rem;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid rgba(49, 51, 63, 0.1);
            background-color: rgba(255, 255, 255, 0.8);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .booth-number {
            font-weight: bold;
            color: #ff6b6b;
            font-size: 1.2em;
        }
        
        .company-name {
            font-size: 1.4em;
            font-weight: 600;
            margin: 0.5rem 0;
            color: #2c3e50;
        }
        
        .interaction-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 0.75rem;
            margin-top: 1rem;
        }
        
        .interaction-button {
            padding: 0.5rem 1rem;
            font-size: 0.9em;
        }
    }
    
    /* Loading spinner */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* System metrics */
    .metrics-warning {
        color: #dc3545;
        font-weight: bold;
    }
    
    .metrics-ok {
        color: #28a745;
    }
    
    /* Search and filter styles */
    .filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
    }
    
    .filter-title {
        font-weight: 600;
        color: #495057;
        margin-bottom: 0.5rem;
    }
    
    /* Map and navigation styles */
    .venue-nav {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    .venue-button {
        padding: 0.5rem 1rem;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        background-color: white;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .venue-button:hover {
        background-color: #f8f9fa;
        border-color: #adb5bd;
    }
    
    .venue-button.active {
        background-color: #007bff;
        color: white;
        border-color: #007bff;
    }
    
    /* Dark mode compatibility */
    @media (prefers-color-scheme: dark) {
        .company-card {
            background-color: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.1);
        }
        
        .company-name {
            color: #f8f9fa;
        }
        
        .industry-tag {
            background-color: rgba(255, 255, 255, 0.1);
            color: #f8f9fa;
            border-color: rgba(255, 255, 255, 0.2);
        }
        
        .interaction-button {
            background-color: rgba(255, 255, 255, 0.1);
            color: #f8f9fa;
            border-color: rgba(255, 255, 255, 0.2);
        }
        
        .filter-section {
            background-color: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.1);
        }
    }
    
    /* Print styles */
    @media print {
        .company-card {
            break-inside: avoid;
            margin-bottom: 1rem;
            padding: 1rem;
            border: 1px solid #000;
        }
        
        .interaction-buttons {
            display: none;
        }
        
        .stButton, .stSelectbox, .stTextInput {
            display: none;
        }
    }
</style>
"""


def get_education_badge_class(education_level: str) -> str:
    """Get CSS class for education level badge"""
    if education_level == "Undergraduate":
        return "education-undergraduate"
    elif education_level == "Postgraduate":
        return "education-postgraduate"
    elif education_level == "Both":
        return "education-both"
    else:
        return "education-unknown"


def get_match_color(percentage: int) -> str:
    """Get color for match percentage"""
    if percentage >= 80:
        return "#28a745"  # Green
    elif percentage >= 60:
        return "#ffc107"  # Yellow
    else:
        return "#dc3545"  # Red
