"""
Authentication module of Ebarimt API client.

Ebarimt API endpoints require OAuth2 Password grant auth.
"""

from .password_grant import PasswordGrantAuth
from .token import OAuth2Token

__all__ = ["OAuth2Token", "PasswordGrantAuth"]
