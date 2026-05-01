from functools import lru_cache
from supabase import Client, create_client
from .config import get_settings


@lru_cache
def admin_client() -> Client:
    s = get_settings()
    return create_client(s.SUPABASE_URL, s.SUPABASE_SECRET_KEY)
