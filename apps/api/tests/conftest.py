import os
import sys
from pathlib import Path

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SECRET_KEY", "sb_secret_test")
os.environ.setdefault("DEV_MOCK_AUTH", "true")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
