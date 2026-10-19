import hashlib
import os
import re
import secrets
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

# Server-side only (e.g. a Hugging Face secret) — never put this in the frontend
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")


def is_admin(x_admin_key: str = Header(default="")) -> bool:
    """True when the request carries the correct X-Admin-Key header."""
    return bool(ADMIN_API_KEY) and secrets.compare_digest(x_admin_key, ADMIN_API_KEY)


def require_admin(x_admin_key: str = Header(default="")):
    """Dependency for destructive/sensitive endpoints."""
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Admin actions are disabled (ADMIN_API_KEY is not set)")
    if not is_admin(x_admin_key):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Key header")


def workspace_owner(x_workspace_id: str = Header(default="")) -> str:
    """
    Each browser sends a random workspace ID it generated itself (no sign-up). Documents are
    tagged with a hash of it, so visitors only see their own uploads and the raw ID is never stored.
    """
    if not re.fullmatch(r"[A-Za-z0-9-]{16,64}", x_workspace_id):
        raise HTTPException(status_code=400, detail="Missing or invalid workspace ID. Please reload the page.")
    return hashlib.sha256(x_workspace_id.encode()).hexdigest()


def client_ip(request: Request) -> str:
    # Behind a proxy (Hugging Face) every request comes from the proxy, so use the
    # address it appended — the rightmost X-Forwarded-For entry can't be spoofed by the client
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """
    Simple in-memory sliding-window limit per client IP.
    Protects the Groq/NewsAPI quota; resets on restart, which is fine for a demo.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.hits: dict[str, deque] = defaultdict(deque)

    def __call__(self, request: Request):
        if self.max_requests <= 0:
            return  # disabled
        now = time.monotonic()
        hits = self.hits[client_ip(request)]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - hits[0])) + 1
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Please wait {retry_after}s and try again.",
                headers={"Retry-After": str(retry_after)},
            )
        hits.append(now)


# Endpoints that call the LLM / NewsAPI
ai_rate_limit = RateLimiter(int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")))
