import json
import functools
from core.redis_client import get_redis

CACHE_TTL = 60

def cached(key_prefix: str, ttl: int = CACHE_TTL):
   
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            r = get_redis()
            key_parts = [str(a) for a in args] + [f"{k}={v}" for k, v in kwargs.items()]
            cache_key = f"{key_prefix}:{':'.join(key_parts)}" if key_parts else key_prefix

            cached_val = r.get(cache_key)
            if cached_val is not None:
                return json.loads(cached_val)

            result = func(*args, **kwargs)
            if result is not None:
                r.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

def invalidate(key_prefix: str, *args):
    r = get_redis()
    if args:
        key_parts = [str(a) for a in args]
        r.delete(f"{key_prefix}:{':'.join(key_parts)}")
    else:
        for key in r.scan_iter(f"{key_prefix}*"):
            r.delete(key)