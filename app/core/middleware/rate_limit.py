"""Rate limiting middleware using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Global default
    storage_uri="memory://",  # In-memory storage (consider Redis for production)
)
