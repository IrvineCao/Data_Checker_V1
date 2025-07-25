import streamlit as st
import functools
from datetime import datetime

def initialize_session_state():
    """
    Initialize all necessary variables in st.session_state 
    if they don't already exist.
    """
    # Existing state variables
    if 'stage' not in st.session_state:
        st.session_state.stage = 'initial'
    if 'params' not in st.session_state:
        st.session_state.params = {}
    if 'df_preview' not in st.session_state:
        st.session_state.df_preview = None
    if 'query_duration' not in st.session_state:
        st.session_state.query_duration = 0
    if 'download_info' not in st.session_state:
        st.session_state.download_info = {}

    # --- USER NOTIFICATIONS ---
    if 'user_message' not in st.session_state:
        st.session_state.user_message = None

def display_user_message():
    """
    Checks and displays any message stored in session_state.
    The message is automatically cleared after display to prevent it from reappearing.
    """
    if st.session_state.get('user_message'):
        message = st.session_state.user_message
        msg_type = message.get("type", "info")
        msg_text = message.get("text", "")

        if msg_type == "error":
            st.error(msg_text, icon="🚨")
        elif msg_type == "warning":
            st.warning(msg_text, icon="⚠️")
        else:
            st.info(msg_text, icon="ℹ️")
        
        # Clear the message after it has been displayed
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