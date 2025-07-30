import streamlit as st
import os

def load_css(css_file):
    """Load and return CSS content"""
    try:
        with open(css_file) as f:
            return f.read()
    except Exception as e:
        st.error(f"Failed to load CSS file: {e}")
        return ""

def apply_animations():
    """Apply animations to the Streamlit app"""
    try:

        css_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'basic.css')
            
        # Debug info
        if not os.path.exists(css_file):
            st.error(f"CSS file not found at: {css_file}")
            return
            
        # Load and inject CSS
        css = load_css(css_file)
        if css:
            st.markdown(f"""
                <style>
                    {css}
                </style>
            """, unsafe_allow_html=True)
            
        # Add some basic animations that will work regardless of CSS file
        st.markdown("""
            <style>
                /* Basic animations that will work regardless of CSS file */
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                .element-container {
                    animation: fadeIn 0.5s ease-in;
                }
                
                div[data-testid="stMarkdownContainer"] > p {
                    animation: fadeIn 1s ease-in;
                }
                
                button {
                    transition: all 0.3s ease !important;
                }
                
                button:hover {
                    transform: scale(1.05) !important;
                }
            </style>
        """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Failed to apply animations: {e}") 