import os
import json
from pathlib import Path
from typing import Optional


class TokenStorage:
    """Securely store and retrieve authentication tokens."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".springforge"
        self.config_dir.mkdir(exist_ok=True, mode=0o700)  # rwx------
        self.token_file = self.config_dir / "auth.json"
    
    def save_token(self, email: str, token: str) -> None:
        """Save authentication token for user."""
        try:
            data = self._load_auth_file()
            data["current_user"] = email
            data["users"] = data.get("users", {})
            data["users"][email] = {
                "token": token,
                "token_type": "bearer"
            }
            self._write_auth_file(data)
        except Exception as e:
            raise Exception(f"Failed to save token: {e}")
    
    def get_token(self, email: Optional[str] = None) -> Optional[str]:
        """Get authentication token for user."""
        try:
            data = self._load_auth_file()
            if not data:
                return None
            
            # Use provided email or current user
            user_email = email or data.get("current_user")
            if not user_email:
                return None
            
            user_data = data.get("users", {}).get(user_email)
            return user_data.get("token") if user_data else None
        except Exception:
            return None
    
    def get_current_user(self) -> Optional[str]:
        """Get currently logged-in user email."""
        try:
            data = self._load_auth_file()
            return data.get("current_user")
        except Exception:
            return None
    
    def remove_token(self, email: Optional[str] = None) -> bool:
        """Remove authentication token (logout)."""
        try:
            data = self._load_auth_file()
            if not data:
                return False
            
            user_email = email or data.get("current_user")
            if not user_email:
                return False
            
            users = data.get("users", {})
            if user_email in users:
                del users[user_email]
            
            if data.get("current_user") == user_email:
                # Switch to another user if available
                remaining_users = list(users.keys())
                data["current_user"] = remaining_users[0] if remaining_users else None
            
            self._write_auth_file(data)
            return True
        except Exception:
            return False
    
    def list_users(self) -> list:
        """List all stored users."""
        try:
            data = self._load_auth_file()
            return list(data.get("users", {}).keys())
        except Exception:
            return []
    
    def clear_all(self) -> bool:
        """Clear all stored tokens (for testing)."""
        try:
            self._write_auth_file({})
            return True
        except Exception:
            return False
    
    def _load_auth_file(self) -> dict:
        """Load auth file content."""
        if not self.token_file.exists():
            return {}
        
        with open(self.token_file, "r") as f:
            return json.load(f) or {}
    
    def _write_auth_file(self, data: dict) -> None:
        """Write auth file with restricted permissions."""
        # Write to temp file first, then move (atomic operation)
        temp_file = self.token_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        
        # Set restrictive permissions before replacing
        os.chmod(temp_file, 0o600)  # rw-------
        temp_file.replace(self.token_file)
        os.chmod(self.token_file, 0o600)


# Global instance
_storage = TokenStorage()


def get_token_storage() -> TokenStorage:
    """Get global token storage instance."""
    return _storage
