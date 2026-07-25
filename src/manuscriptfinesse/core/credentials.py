"""
Secure Credential Storage for ManuscriptFinesse

This module handles secure storage and retrieval of API keys and other
sensitive credentials using environment variables and optional encrypted storage.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import getpass


class CredentialManager:
    """Manages secure storage and retrieval of API credentials."""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the credential manager.

        Args:
            config_dir: Directory to store credential files. Defaults to ~/.manuscriptfinesse
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".manuscriptfinesse"

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_file = self.config_dir / "credentials.json"
        self.key_file = self.config_dir / ".key"

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            return key

    def _get_cipher(self) -> Fernet:
        """Get cipher instance for encryption/decryption."""
        key = self._get_or_create_key()
        return Fernet(key)

    def save_credential(self, provider: str, api_key: str, encrypt: bool = True) -> None:
        """
        Save an API credential securely.

        Args:
            provider: Name of the provider (e.g., 'gemini', 'openrouter', 'openai')
            api_key: The API key to store
            encrypt: Whether to encrypt the credential (default: True)
        """
        credentials = self._load_credentials()

        if encrypt:
            cipher = self._get_cipher()
            encrypted_key = cipher.encrypt(api_key.encode()).decode()
            credentials[provider] = {"encrypted": True, "value": encrypted_key}
        else:
            credentials[provider] = {"encrypted": False, "value": api_key}

        self._save_credentials(credentials)

    def get_credential(self, provider: str) -> Optional[str]:
        """
        Retrieve an API credential.

        Args:
            provider: Name of the provider

        Returns:
            The API key if found, None otherwise
        """
        # First check environment variables
        env_var_map = {
            "gemini": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "ollama": "OLLAMA_API_KEY",
        }

        if provider in env_var_map:
            env_value = os.getenv(env_var_map[provider])
            if env_value:
                return env_value

        # Then check stored credentials
        credentials = self._load_credentials()
        if provider not in credentials:
            return None

        cred_data = credentials[provider]
        if cred_data.get("encrypted"):
            cipher = self._get_cipher()
            try:
                decrypted = cipher.decrypt(cred_data["value"].encode()).decode()
                return decrypted
            except Exception:
                return None
        else:
            return cred_data.get("value")

    def list_providers(self) -> list:
        """List all providers with stored credentials."""
        credentials = self._load_credentials()
        return list(credentials.keys())

    def has_credential(self, provider: str) -> bool:
        """Check if a credential exists for a provider."""
        # Check environment variable first
        env_var_map = {
            "gemini": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "ollama": "OLLAMA_API_KEY",
        }

        if provider in env_var_map and os.getenv(env_var_map[provider]):
            return True

        credentials = self._load_credentials()
        return provider in credentials

    def delete_credential(self, provider: str) -> bool:
        """
        Delete a credential.

        Args:
            provider: Name of the provider

        Returns:
            True if deleted, False if not found
        """
        credentials = self._load_credentials()
        if provider in credentials:
            del credentials[provider]
            self._save_credentials(credentials)
            return True
        return False

    def _load_credentials(self) -> Dict:
        """Load credentials from file."""
        if not self.credentials_file.exists():
            return {}

        try:
            with open(self.credentials_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_credentials(self, credentials: Dict) -> None:
        """Save credentials to file."""
        with open(self.credentials_file, "w") as f:
            json.dump(credentials, f, indent=2)
        # Set restrictive permissions
        os.chmod(self.credentials_file, 0o600)


# Global instance for convenience
_default_manager: Optional[CredentialManager] = None


def get_credential_manager() -> CredentialManager:
    """Get the default credential manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = CredentialManager()
    return _default_manager


def save_api_key(provider: str, api_key: str, encrypt: bool = True) -> None:
    """Convenience function to save an API key."""
    get_credential_manager().save_credential(provider, api_key, encrypt)


def get_api_key(provider: str) -> Optional[str]:
    """Convenience function to get an API key."""
    return get_credential_manager().get_credential(provider)


def has_api_key(provider: str) -> bool:
    """Convenience function to check if an API key exists."""
    return get_credential_manager().has_credential(provider)
