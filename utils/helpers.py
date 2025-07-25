import streamlit as st
from pathlib import Path

# Define the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

def initialize_session_state():
    """Initialize necessary variables in st.session_state if they don't exist."""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Home'
    if 'user_message' not in st.session_state:
        st.session_state.user_message = None