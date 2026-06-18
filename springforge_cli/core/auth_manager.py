import httpx
from springforge_cli.utils.config import REQUEST_TIMEOUT, MAX_RETRIES
from springforge_cli.utils.logger import error, warn, step, success
from springforge_cli.core.token_storage import get_token_storage


class AuthManager:
    """Manage authentication with FastAPI server."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=REQUEST_TIMEOUT)
        self.storage = get_token_storage()
    
    def register(self, name: str, email: str, password: str) -> bool:
        """Register a new user."""
        try:
            step("Registering user...")
            response = self.client.post(
                f"{self.base_url}/api/register",
                json={
                    "name": name,
                    "email": email,
                    "password": password
                }
            )
            response.raise_for_status()
            result = response.json()
            success(f"User registered: {result.get('email', email)}")
            return True
        except httpx.HTTPStatusError as e:
            body = e.response.json() if e.response.headers.get("content-type") == "application/json" else e.response.text
            detail = body.get("detail") if isinstance(body, dict) else str(body)
            error(f"Registration failed: {detail}")
            return False
        except Exception as e:
            error(f"Registration error: {e}")
            return False
    
    def login(self, email: str, password: str) -> bool:
        """Login user and store token."""
        try:
            step("Authenticating...")
            response = self.client.post(
                f"{self.base_url}/api/login",
                json={
                    "email": email,
                    "password": password
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if "access_token" in result:
                token = result["access_token"]
                self.storage.save_token(email, token)
                success(f"Logged in as {email}")
                return True
            else:
                error("No token received from server")
                return False
        except httpx.HTTPStatusError as e:
            body = e.response.json() if e.response.headers.get("content-type") == "application/json" else e.response.text
            detail = body.get("detail") if isinstance(body, dict) else str(body)
            error(f"Login failed: {detail}")
            return False
        except Exception as e:
            error(f"Login error: {e}")
            return False
    
    def logout(self, email: str = None) -> bool:
        """Logout user and remove token."""
        try:
            user = email or self.storage.get_current_user()
            if not user:
                warn("No user logged in")
                return False
            
            if self.storage.remove_token(user):
                success(f"Logged out from {user}")
                return True
            else:
                error("Logout failed")
                return False
        except Exception as e:
            error(f"Logout error: {e}")
            return False
    
    def get_current_user(self) -> str:
        """Get current logged-in user."""
        return self.storage.get_current_user() or "Unknown"
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self.storage.get_current_user() is not None
    
    def list_users(self) -> list:
        """List all stored users."""
        return self.storage.list_users()


def get_auth_manager(base_url: str) -> AuthManager:
    """Create auth manager instance."""
    return AuthManager(base_url)
