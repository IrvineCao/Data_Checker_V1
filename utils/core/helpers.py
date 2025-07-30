import streamlit as st
from pathlib import Path
import functools
from datetime import datetime

# Define the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

def initialize_session_state():
    """Initialize necessary variables in st.session_state if they don't exist."""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Home'
    if 'user_message' not in st.session_state:
        st.session_state.user_message = None

def trace_function_call(func):
    """A decorator to trace function calls and log them to the session state."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'call_trace' not in st.session_state:
            st.session_state.call_trace = []

        call_log = {
            "function": func.__name__,
            "module": func.__module__,
            "timestamp": datetime.now().isoformat(),
            "status": "start",
            "args": str(args),
            "kwargs": str(kwargs)
        }
        st.session_state.call_trace.append(call_log)

        try:
            result = func(*args, **kwargs)
            st.session_state.call_trace.append({
                "function": func.__name__,
                "status": "finish",
                "timestamp": datetime.now().isoformat(),
                "return_value": str(result)[:200]  # Truncate long return values
            })
            return result
        except Exception as e:
            st.session_state.call_trace.append({
                "function": func.__name__,
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            raise e
    return wrapper

def display_call_trace():
    """Displays the call trace in a Streamlit expander."""
    with st.expander("Show Debug Trace"):
        if st.session_state.get('call_trace'):
            st.json(st.session_state.call_trace)
        else:
            st.write("No calls have been traced yet.")