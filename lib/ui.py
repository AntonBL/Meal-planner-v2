"""UI Module - Custom Styling and Components.

This module handles the visual presentation of the app, injecting custom CSS
and providing reusable UI components for a consistent, premium feel.
"""


import streamlit as st

# ============================================================================
# CSS STYLING
# ============================================================================

def load_css() -> str:
    """Define the custom CSS for the application."""
    return """
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

        /* Root Variables */
        :root {
            --primary-color: #FF4B4B;
            --background-color: #0E1117;
            --secondary-background-color: #262730;
            --text-color: #FAFAFA;
            --font-heading: 'Outfit', sans-serif;
            --font-body: 'Inter', sans-serif;
            --card-radius: 12px;
            --card-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            --transition-speed: 0.2s;
        }

        /* Global Typography */
        html, body, [class*="css"] {
            font-family: var(--font-body);
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: var(--font-heading);
            font-weight: 600;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.5rem !important;
            background: linear-gradient(120deg, #FF4B4B, #FF914D);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding-bottom: 0.5rem;
        }

        /* Custom Card Component */
        .stCard {
            background-color: var(--secondary-background-color);
            border-radius: var(--card-radius);
            padding: 1.5rem;
            box-shadow: var(--card-shadow);
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: transform var(--transition-speed), box-shadow var(--transition-speed);
        }

        .stCard:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
            border-color: rgba(255, 75, 75, 0.3);
        }

        /* Metrics Styling */
        [data-testid="stMetric"] {
            background-color: var(--secondary-background-color);
            padding: 1rem;
            border-radius: var(--card-radius);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        [data-testid="stMetricLabel"] {
            font-family: var(--font-heading);
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.7);
        }

        [data-testid="stMetricValue"] {
            font-family: var(--font-heading);
            font-weight: 700;
            color: var(--primary-color);
        }

        /* Button Styling */
        .stButton button {
            border-radius: 8px;
            font-family: var(--font-heading);
            font-weight: 500;
            transition: all 0.2s ease;
            border: none;
        }

        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }

        /* Primary Button Gradient */
        .stButton button[kind="primary"] {
            background: linear-gradient(90deg, #FF4B4B, #FF914D);
            color: white;
            border: none;
        }

        /* Expander Styling */
        .streamlit-expanderHeader {
            background-color: var(--secondary-background-color);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            font-family: var(--font-heading);
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0E1117;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }

        /* Custom Classes */
        .highlight-text {
            color: var(--primary-color);
            font-weight: 600;
        }

        .subtle-text {
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.9rem;
        }

        /* Hide Streamlit Elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Hide form helper text */
        .stTextInput > div > div > input + div {
            display: none;
        }

    </style>
    """

def apply_styling():
    """Apply the custom CSS to the current page."""
    st.markdown(load_css(), unsafe_allow_html=True)

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_header(title: str, subtitle: str = None, icon: str = None):
    """Render a consistent page header."""
    if icon:
        st.title(f"{icon} {title}")
    else:
        st.title(title)

    if subtitle:
        st.markdown(f"<p class='subtle-text' style='margin-top: -1rem; margin-bottom: 2rem;'>{subtitle}</p>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

def render_card(content: str, title: str = None, icon: str = None):
    """Render a content card."""
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    if title:
        icon_html = f"<span>{icon}</span> " if icon else ""
        st.markdown(f"### {icon_html}{title}")
    st.markdown(content)
    st.markdown('</div>', unsafe_allow_html=True)

def render_metric_card(label: str, value: str, delta: str = None, icon: str = None):
    """Render a styled metric card."""
    # We use standard st.metric but it's styled via CSS
    # icon is currently unused but kept for API compatibility/future use
    _ = icon
    """Render a styled metric card."""
    # We use standard st.metric but it's styled via CSS
    st.metric(label=label, value=value, delta=delta)
