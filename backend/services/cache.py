"""
Redis Cache Service
Provides caching decorators for rhyme lookups and AI responses.
Falls back gracefully when Redis is unavailable.
"""
import os
import json
import hashlib
import functools
from typing import Optional, Callable, Any
import asyncio

# Redis is optional - only used in Docker environment
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Redis connection
_redis_client: Optional[Any] = None


async def get_redis() -> Optional[Any]:
    """Get or create Redis connection."""
    global _redis_client
    
    if not REDIS_AVAILABLE:
        return None
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            await _redis_client.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}")
            _redis_client = None
    
    return _redis_client


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 3600, prefix: str = "vibelyrics"):
    """
    Decorator for caching async function results in Redis.
    
    Args:
        ttl: Time-to-live in seconds (default: 1 hour)
        prefix: Cache key prefix
    
    Usage:
        @cached(ttl=3600, prefix="rhymes")
        async def get_rhymes(word: str) -> list:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            client = await get_redis()
            if client:
                try:
                    cached_value = await client.get(key)
                    if cached_value:
                        return json.loads(cached_value)
                except Exception as e:
                    print(f"Cache read error: {e}")
            
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Store in cache
            if client and result is not None:
                try:
                    await client.setex(key, ttl, json.dumps(result, default=str))
                except Exception as e:
                    print(f"Cache write error: {e}")
            
            return result
        
        return wrapper
    return decorator


async def invalidate_cache(pattern: str = "*"):
    """Invalidate cache entries matching pattern."""
    client = await get_redis()
    if client:
        try:
            keys = await client.keys(f"vibelyrics:{pattern}")
            if keys:
                await client.delete(*keys)
        except Exception as e:
            print(f"Cache invalidation error: {e}")


async def close_redis():
    """Close Redis connection on shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
