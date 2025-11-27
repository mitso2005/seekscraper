"""Persistent cache for company phone numbers."""

import json
import os
from threading import Lock
from datetime import datetime

CACHE_FILE = os.path.join("cache", "company_phone_cache.json")
cache_lock = Lock()


class PhoneCache:
    """Thread-safe persistent phone number cache."""
    
    def __init__(self, cache_file=CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Loaded {len(data)} cached phone numbers")
                    return data
            except Exception as e:
                print(f"WARNING: Error loading cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"WARNING: Error saving cache: {e}")
    
    def get(self, company_name):
        """Get phone number from cache (thread-safe)."""
        with cache_lock:
            entry = self.cache.get(company_name)
            if entry:
                return entry.get('phone', '')
            return None
    
    def set(self, company_name, phone_number, location=''):
        """Set phone number in cache (thread-safe)."""
        with cache_lock:
            self.cache[company_name] = {
                'phone': phone_number,
                'location': location,
                'cached_at': datetime.now().isoformat()
            }
            self._save_cache()
    
    def has(self, company_name):
        """Check if company exists in cache."""
        with cache_lock:
            return company_name in self.cache
    
    def get_stats(self):
        """Get cache statistics."""
        with cache_lock:
            total = len(self.cache)
            with_phone = sum(1 for e in self.cache.values() if e.get('phone'))
            return {
                'total_companies': total,
                'with_phone': with_phone,
                'without_phone': total - with_phone
            }
