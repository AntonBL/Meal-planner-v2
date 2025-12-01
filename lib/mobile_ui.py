"""Mobile-optimized UI components and utilities."""

import streamlit as st


def mobile_card(title: str, content: str, icon: str = "📋", actions=None):
    """
    Render a mobile-friendly card component.
    
    Args:
        title: Card title
        content: Card content (can be markdown)
        icon: Emoji icon for the card
        actions: Optional list of button configs [(label, callback), ...]
    """
    with st.container():
        st.markdown(f"""
        <div style="
            background-color: #F8F9FA;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            border-left: 4px solid #FF6B35;
        ">
            <h3 style="margin: 0 0 8px 0; font-size: 18px;">
                {icon} {title}
            </h3>
            <div style="font-size: 16px; line-height: 1.5;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if actions:
            cols = st.columns(len(actions))
            for i, (label, callback) in enumerate(actions):
                with cols[i]:
                    if st.button(label, key=f"action_{title}_{i}", use_container_width=True):
                        callback()


def mobile_section_header(title: str, icon: str = ""):
    """
    Render a mobile-friendly section header.
    
    Args:
        title: Section title
        icon: Optional emoji icon
    """
    st.markdown(f"""
    <div style="
        font-size: 20px;
        font-weight: 600;
        margin: 24px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #FF6B35;
    ">
        {icon} {title}
    </div>
    """, unsafe_allow_html=True)


def mobile_button(label: str, icon: str = "", primary: bool = False, full_width: bool = True):
    """
    Render a mobile-friendly button with larger touch target.
    
    Args:
        label: Button label
        icon: Optional emoji icon
        primary: Whether this is a primary action button
        full_width: Whether button should span full width
        
    Returns:
        True if button was clicked
    """
    button_type = "primary" if primary else "secondary"
    return st.button(
        f"{icon} {label}" if icon else label,
        type=button_type,
        use_container_width=full_width,
        key=f"mobile_btn_{label.replace(' ', '_')}"
    )


def mobile_checkbox_list(items: list[dict], on_change=None):
    """
    Render a mobile-friendly checkbox list with larger touch targets.
    
    Args:
        items: List of dicts with 'label', 'checked', 'key' keys
        on_change: Optional callback when checkbox changes
        
    Returns:
        Dict of checkbox states {key: bool}
    """
    states = {}
    
    for item in items:
        # Larger spacing for mobile
        st.markdown("<div style='margin: 12px 0;'>", unsafe_allow_html=True)
        states[item['key']] = st.checkbox(
            item['label'],
            value=item.get('checked', False),
            key=item['key'],
            on_change=on_change
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    return states


def mobile_tabs(tabs: list[str]):
    """
    Create mobile-friendly tabs with better spacing.
    
    Args:
        tabs: List of tab labels
        
    Returns:
        Streamlit tabs object
    """
    return st.tabs([f"**{tab}**" for tab in tabs])


def mobile_metric(label: str, value: str, delta: str = None, icon: str = ""):
    """
    Display a mobile-friendly metric card.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta/change value
        icon: Optional emoji icon
    """
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #FF6B35 0%, #FF8C61 100%);
        color: white;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        text-align: center;
    ">
        <div style="font-size: 14px; opacity: 0.9; margin-bottom: 4px;">
            {icon} {label}
        </div>
        <div style="font-size: 28px; font-weight: 700;">
            {value}
        </div>
        {f'<div style="font-size: 14px; margin-top: 4px;">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def mobile_collapsible(title: str, content_func, icon: str = "▶️", default_open: bool = False):
    """
    Create a mobile-friendly collapsible section.
    
    Args:
        title: Section title
        content_func: Function to render content when expanded
        icon: Icon for the expander
        default_open: Whether section starts expanded
    """
    with st.expander(f"{icon} **{title}**", expanded=default_open):
        content_func()


def add_mobile_styles():
    """
    Inject custom CSS for mobile-optimized styling.
    Call this at the top of each page.
    """
    st.markdown("""
    <style>
    /* Mobile-first responsive design */
    
    /* Larger touch targets */
    .stButton > button {
        min-height: 48px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
    }
    
    /* Better checkbox spacing */
    .stCheckbox {
        padding: 8px 0 !important;
    }
    
    .stCheckbox > label {
        font-size: 16px !important;
        min-height: 44px !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* Larger text inputs */
    .stTextInput > div > div > input {
        font-size: 16px !important;
        min-height: 48px !important;
    }
    
    .stTextArea > div > div > textarea {
        font-size: 16px !important;
    }
    
    /* Better select boxes */
    .stSelectbox > div > div > select {
        font-size: 16px !important;
        min-height: 48px !important;
    }
    
    /* Improved tabs for mobile */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 16px !important;
        padding: 12px 16px !important;
        border-radius: 8px 8px 0 0 !important;
    }
    
    /* Better expander styling */
    .streamlit-expanderHeader {
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 12px !important;
    }
    
    /* Improved metric display */
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
    }
    
    /* Better spacing in columns */
    [data-testid="column"] {
        padding: 0 8px !important;
    }
    
    /* Reduce sidebar width on mobile */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            width: 280px !important;
        }
    }
    
    /* Hide hamburger menu on desktop, show on mobile */
    @media (min-width: 769px) {
        button[kind="header"] {
            display: none !important;
        }
    }
    
    /* Sticky action buttons at bottom */
    .sticky-bottom {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 12px 0;
        border-top: 1px solid #e0e0e0;
        z-index: 100;
    }
    
    /* Card shadows for depth */
    .card {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: box-shadow 0.2s;
    }
    
    .card:active {
        box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)
