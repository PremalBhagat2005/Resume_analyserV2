import os
import json
import hashlib
import redis

redis_url = os.getenv("REDIS_URL")
if redis_url:
    cache_client = redis.Redis.from_url(redis_url, decode_responses=True)
else:
    cache_client = None

def get_cache_key(prefix: str, content: str) -> str:
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    return f"{prefix}:{content_hash}"

def get_cached_json(key: str):
    if not cache_client:
        return None
    try:
        val = cache_client.get(key)
        if val:
            return json.loads(val)
    except Exception as e:
        print(f"[CACHE] Get error for {key}: {e}")
    return None

def set_cached_json(key: str, data: dict, expire_seconds: int = 86400):
    if not cache_client:
        return
    try:
        cache_client.setex(key, expire_seconds, json.dumps(data))
    except Exception as e:
        print(f"[CACHE] Set error for {key}: {e}")
