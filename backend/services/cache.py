"""
In-Memory TTL Cache Service
Provides caching for rhyme lookups and AI responses.
Works out of the box — no external dependencies required.
"""
import json
import hashlib
import functools
import time
import threading
from typing import Optional, Callable, Any, Dict, Tuple

# ── Thread-safe in-memory TTL cache ─────────────────────────────────

_cache_store: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expire_time)
_cache_lock = threading.Lock()
_MAX_CACHE_SIZE = 2000  # evict oldest when exceeded


def _cache_get(key: str) -> Optional[Any]:
    """Get value from cache if not expired."""
    with _cache_lock:
        entry = _cache_store.get(key)
        if entry is None:
            return None
        value, expire_time = entry
        if time.time() > expire_time:
            del _cache_store[key]
            return None
        return value


def _cache_set(key: str, value: Any, ttl: int):
    """Set value in cache with TTL (seconds)."""
    with _cache_lock:
        # Simple eviction: if we're over the limit, drop the oldest 25%
        if len(_cache_store) >= _MAX_CACHE_SIZE:
            sorted_keys = sorted(
                _cache_store.keys(),
                key=lambda k: _cache_store[k][1]  # sort by expire time
            )
            for k in sorted_keys[:_MAX_CACHE_SIZE // 4]:
                del _cache_store[k]
        _cache_store[key] = (value, time.time() + ttl)


# ── Public API ──────────────────────────────────────────────────────

def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 3600, prefix: str = "vibelyrics"):
    """
    Decorator for caching function results in memory with TTL.

    Works for both sync and async functions.

    Usage:
        @cached(ttl=3600, prefix="rhymes")
        async def get_rhymes(word: str) -> list:
            ...
    """
    def decorator(func: Callable) -> Callable:
        import asyncio

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                key = f"{prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
                cached_value = _cache_get(key)
                if cached_value is not None:
                    return cached_value
                result = await func(*args, **kwargs)
                if result is not None:
                    _cache_set(key, result, ttl)
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                key = f"{prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
                cached_value = _cache_get(key)
                if cached_value is not None:
                    return cached_value
                result = func(*args, **kwargs)
                if result is not None:
                    _cache_set(key, result, ttl)
                return result
            return sync_wrapper

    return decorator


def invalidate_cache(pattern: str = "*"):
    """Invalidate cache entries matching pattern (supports * wildcard at end)."""
    with _cache_lock:
        if pattern == "*":
            _cache_store.clear()
            return
        prefix = f"vibelyrics:{pattern.rstrip('*')}"
        to_delete = [k for k in _cache_store if k.startswith(prefix)]
        for k in to_delete:
            del _cache_store[k]


async def close_redis():
    """No-op — kept for backward compatibility."""
    pass


class PersistentCache:
    """Persistent DB-backed cache using CacheEntry model."""
    
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        from datetime import datetime, timezone
        from sqlalchemy import select
        from backend.database import async_session
        from backend.models import CacheEntry

        try:
            async with async_session() as session:
                query = select(CacheEntry).where(CacheEntry.key == key)
                res = await session.execute(query)
                entry = res.scalars().first()
                if entry:
                    now = datetime.now(timezone.utc)
                    if entry.expires_at.tzinfo is None:
                        now = now.replace(tzinfo=None)
                    if now > entry.expires_at:
                        await session.delete(entry)
                        await session.commit()
                        return None
                    return json.loads(entry.value)
        except Exception:
            # Fallback to in-memory cache if DB is not available
            return _cache_get(key)
        return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int):
        from datetime import datetime, timezone, timedelta
        from sqlalchemy import select
        from backend.database import async_session
        from backend.models import CacheEntry

        serialized = json.dumps(value)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl)
        
        try:
            async with async_session() as session:
                if expires_at.tzinfo is not None:
                    expires_at = expires_at.replace(tzinfo=None)
                
                query = select(CacheEntry).where(CacheEntry.key == key)
                res = await session.execute(query)
                entry = res.scalars().first()
                if entry:
                    entry.value = serialized
                    entry.expires_at = expires_at
                else:
                    entry = CacheEntry(key=key, value=serialized, expires_at=expires_at)
                    session.add(entry)
                await session.commit()
        except Exception:
            # Fallback to in-memory cache if DB is not available
            _cache_set(key, value, ttl)


def persistent_cached(ttl: int = 3600, prefix: str = "vibelyrics"):
    """
    Decorator for caching function results in persistent CacheEntry table.
    Falls back to in-memory caching if database fails.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            cached_value = await PersistentCache.get(key)
            if cached_value is not None:
                return cached_value
            result = await func(*args, **kwargs)
            if result is not None:
                await PersistentCache.set(key, result, ttl)
            return result
        return wrapper
    return decorator

