import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from rest_framework.test import APIClient
import json

client = APIClient()

print("=================================================================")
print("AUDIT: /api/anime/38000/watch-options/?country=IN")
print("=================================================================")
r_watch = client.get('/api/anime/38000/watch-options/?country=IN')
print(f"Status Code: {r_watch.status_code}")
data_watch = r_watch.json()
print("Top-level keys:", list(data_watch.keys()))
print("Results Count:", data_watch.get("results_count"))
print("Categories summary:")
for cat, items in data_watch.get("categories", {}).items():
    print(f"  {cat}: {len(items)} items")
    for it in items:
        print(f"    -> [{it.get('provider_name')}] URL: {it.get('url')} | Logo: {it.get('provider_logo_url')} | Category: {it.get('category')} | Country: {it.get('country')} | Verified At: {it.get('last_verified_at')}")

print("\n=================================================================")
print("AUDIT: /api/anime/38000/trailers/")
print("=================================================================")
r_trailers = client.get('/api/anime/38000/trailers/')
print(f"Status Code: {r_trailers.status_code}")
data_trailers = r_trailers.json()
print("Top-level keys:", list(data_trailers.keys()))
print("Trailer Count:", data_trailers.get("count"))
for t in data_trailers.get("trailers", [])[:2]:
    print(f"  -> Title: '{t.get('title')}' | Uploader: '{t.get('uploader_name')}' ({t.get('uploader_url')}) | YT ID: {t.get('youtube_id')} | Official: {t.get('is_official')} | Embed: {t.get('embed_url')}")

print("\n=================================================================")
print("AUDIT: /api/anime/watchmode-status/")
print("=================================================================")
r_wm = client.get('/api/anime/watchmode-status/')
print(f"Status Code: {r_wm.status_code}")
data_wm = r_wm.json()
print("Watchmode status payload:", json.dumps(data_wm, indent=2))
