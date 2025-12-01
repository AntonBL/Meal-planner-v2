"""
Authentication Module
Encapsulated authentication logic using streamlit-authenticator.
Can be easily enabled/disabled with the ENABLE_AUTH flag.
"""

import logging
import os

import streamlit as st

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ============================================================================
# CONFIGURATION - Toggle authentication here
# ============================================================================
ENABLE_AUTH = True  # Set to False to disable authentication
MAX_LOGIN_ATTEMPTS = 5  # Maximum failed login attempts before lockout

# ============================================================================
# Authentication Implementation
# ============================================================================

def setup_authentication():
    """
    Set up and handle authentication.

    Returns:
        tuple: (authenticated: bool, name: str, username: str, authenticator: object)
               - authenticated: True if user is authenticated, False otherwise
               - name: Display name of authenticated user (None if not authenticated)
               - username: Username of authenticated user (None if not authenticated)
               - authenticator: Authenticator object for logout (None if auth disabled)

    Usage:
        authenticated, name, username, authenticator = setup_authentication()
        if not authenticated:
            st.stop()  # Stop execution if not authenticated
    """

    logger.info("=== setup_authentication() called ===")

    if not ENABLE_AUTH:
        logger.info("Authentication disabled, returning guest credentials")
        # Authentication disabled - return success with default values
        return True, "Guest", "guest", None

    # Import here to avoid dependency if auth is disabled
    import streamlit_authenticator as stauth

    # Get credentials from environment variables
    auth_username = os.getenv('AUTH_USERNAME', 'roger')
    auth_password = os.getenv('AUTH_PASSWORD')

    logger.info(f"AUTH_USERNAME from env: {auth_username}")
    logger.info(f"AUTH_PASSWORD exists: {bool(auth_password)}")

    if not auth_password:
        logger.error("AUTH_PASSWORD not set in environment")
        st.error("🔒 Authentication Error")
        st.warning("AUTH_PASSWORD not set in .env file")
        st.info("Please add AUTH_USERNAME and AUTH_PASSWORD to your .env file")
        st.code("AUTH_USERNAME=your_username\nAUTH_PASSWORD=your_password")
        st.stop()
        return False, None, None, None

    # Build config from environment variables with plaintext password
    # streamlit-authenticator will hash it automatically with auto_hash=True
    config = {
        'credentials': {
            'usernames': {
                auth_username: {
                    'email': f'{auth_username}@example.com',
                    'name': auth_username.capitalize(),
                    'password': auth_password  # Pass plaintext - will be auto-hashed
                }
            }
        },
        'cookie': {
            'expiry_days': 30,
            'key': os.getenv('AUTH_COOKIE_KEY', 'meal_planner_secret_key_a9fc6a257a3c3ff125aeafcf65ae9061'),
            'name': 'meal_planner_auth_v2'  # Changed name to invalidate old cookies
        }
    }

    # Create authenticator
    try:
        logger.info("Creating Authenticate object...")
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
            auto_hash=True  # Let it hash the password automatically
        )
        logger.info("Authenticate object created successfully")
    except Exception as e:
        logger.error(f"Error creating authenticator: {e}", exc_info=True)
        st.error(f"Error creating authenticator: {e}")
        return False, None, None, None

    # Render login form and get status
    try:
        logger.info("Calling authenticator.login()...")
        logger.info(f"Session state keys before login: {list(st.session_state.keys())}")

        # Call login - this should render the form
        result = authenticator.login(
            location='main',
            max_login_attempts=MAX_LOGIN_ATTEMPTS
        )

        logger.info(f"Session state keys after login: {list(st.session_state.keys())}")
        logger.info(f"login() returned: {result} (type: {type(result)})")

        # Check session state for authentication info
        if 'authentication_status' in st.session_state:
            logger.info(f"Found authentication_status in session: {st.session_state['authentication_status']}")
            logger.info(f"Found name in session: {st.session_state.get('name')}")
            logger.info(f"Found username in session: {st.session_state.get('username')}")

        # Handle case where login() returns None
        # Check session state instead
        if result is None and 'authentication_status' in st.session_state:
            logger.info("login() returned None but found auth in session state")
            name = st.session_state.get('name')
            authentication_status = st.session_state.get('authentication_status')
            username = st.session_state.get('username')
        elif result is None:
            logger.info("login() returned None - treating as not authenticated")
            # Treat as not logged in yet
            name, authentication_status, username = None, None, None
        else:
            name, authentication_status, username = result
            logger.info(f"Unpacked: name={name}, auth_status={authentication_status}, user={username}")

    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        st.error(f"🔒 Authentication Error: {e}")
        import traceback
        st.code(traceback.format_exc())
        st.stop()  # Block access completely
        return False, None, None, None

    # Check authentication status - BLOCK if not authenticated
    if authentication_status is False:
        logger.warning("Authentication failed - incorrect credentials")
        st.error('🔒 Username/password is incorrect')
        st.warning(f'⚠️ Maximum {MAX_LOGIN_ATTEMPTS} failed attempts allowed before lockout')
        st.stop()  # Block access completely
        return False, None, None, authenticator

    if authentication_status is None:
        logger.info("Authentication status is None - showing login form")
        # Don't show extra message - login form should already be visible
        st.stop()  # Block access completely
        return False, None, None, authenticator

    # Successfully authenticated
    logger.info(f"Successfully authenticated user: {name} ({username})")
    return True, name, username, authenticator


def render_logout_button(authenticator, name):
    """
    Render logout button in the sidebar.

    Args:
        authenticator: The authenticator object (can be None if auth disabled)
        name: Display name of the user (can be None)
    """

    if not ENABLE_AUTH or authenticator is None:
        # Authentication disabled or not available
        return

    try:
        with st.sidebar:
            st.markdown(f'## Welcome, {name}!')
            authenticator.logout(location='sidebar')
            st.markdown("---")
    except Exception as e:
        st.sidebar.error(f"Error rendering logout: {e}")


def clear_auth_cookies():
    """
    Utility page to clear authentication cookies.
    Navigate to this URL: /clear_auth
    """
    import streamlit as st
    from streamlit.components.v1 import html

    st.title("Clear Authentication")
    st.warning("Clearing authentication cookies...")

    # Clear streamlit session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # JavaScript to clear cookies
    html("""
        <script>
        // Clear all cookies
        document.cookie.split(";").forEach(function(c) {
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });

        // Clear local storage
        localStorage.clear();

        // Clear session storage
        sessionStorage.clear();

        alert("Cookies cleared! Redirecting to home...");
        window.location.href = "/";
        </script>
    """, height=0)

    st.success("Authentication cleared! Redirecting...")


def is_auth_enabled():
    """
    Check if authentication is enabled.

    Returns:
        bool: True if authentication is enabled, False otherwise
    """
    return ENABLE_AUTH


def require_authentication():
    """
    Convenience function that handles all authentication in one call.

    This function:
    1. Sets up authentication
    2. Blocks access if not authenticated
    3. Renders logout button in sidebar

    Usage in any page:
        from lib.auth import require_authentication
        require_authentication()

        # Rest of your page code here...

    Returns:
        tuple: (name: str, username: str) - authenticated user info
    """
    logger.info("=== require_authentication() called ===")
    authenticated, name, username, authenticator = setup_authentication()

    logger.info(f"setup_authentication returned: authenticated={authenticated}, name={name}, username={username}")

    if not authenticated:
        logger.info("Not authenticated - calling st.stop()")
        st.stop()

    # Render logout button in sidebar
    logger.info("Rendering logout button...")
    render_logout_button(authenticator, name)

    logger.info(f"require_authentication() returning: ({name}, {username})")
    return name, username
