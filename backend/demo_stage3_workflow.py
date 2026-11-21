import os
import sys
import json
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from apps.profiles.models import User
from apps.core.middleware import SESSION_COOKIE_NAME

def run_demonstration():
    print("=" * 70)
    print("ANIMEVERSE AI - STAGE 3 API ENDPOINTS DEMONSTRATION")
    print("=" * 70)

    client = APIClient()

    # Step 1: Initialize visitor session
    print("\n[Step 1] Visiting Dashboard to initialize demo session...")
    res = client.get('/api/dashboard/')
    assert res.status_code == 200
    session_cookie = client.cookies.get(SESSION_COOKIE_NAME)
    assert session_cookie is not None
    session_key = session_cookie.value
    user = User.objects.get(session_key=session_key)
    print(f"Session established: {session_key[:16]}... | User: {user.display_name} (ID: {user.id})")
    print(f"Initial Dashboard Stats: {json.dumps(res.data['stats'], indent=2)}")

    # Step 2: Search for a real anime (e.g. 'Death Note')
    print("\n[Step 2] Searching for real anime: 'Death Note'...")
    res = client.get('/api/anime/search/?q=Death%20Note')
    assert res.status_code == 200
    results = res.data['results']
    print(f"Search succeeded with {len(results)} items found.")
    first_anime = results[0]
    mal_id = first_anime['mal_id']
    print(f"Top result: '{first_anime['title']}' (MAL ID: {mal_id}, Type: {first_anime['anime_type']}, Episodes: {first_anime['total_episodes']}, Source: {first_anime.get('metadata_source')})")

    # Step 3: Open anime details
    print(f"\n[Step 3] Fetching anime details for MAL ID {mal_id}...")
    res = client.get(f'/api/anime/{mal_id}/')
    assert res.status_code == 200
    details = res.data
    print(f"Title: {details['title']}")
    print(f"Genres: {', '.join(details['genres'])}")
    print(f"Score: {details['score']} | Episodes: {details['episodes']}")
    print(f"Synopsis preview: {details['synopsis'][:150]}...")
    print(f"Metadata Source: {details.get('metadata_source')}")

    # Step 4: Add anime to watchlist
    print(f"\n[Step 4] Adding '{details['title']}' to Watchlist with status 'Watching'...")
    res = client.post('/api/list/', {'mal_id': mal_id, 'status': 'Watching'}, format='json')
    assert res.status_code == 201
    entry_id = res.data['id']
    print(f"Added successfully! Entry ID: {entry_id}, Status: {res.data['status']}, Watched: {res.data['watched_episodes']}")

    # Step 5: Update watched episode progress
    print(f"\n[Step 5] Updating watched episodes for Entry {entry_id} to 15...")
    res = client.put(f'/api/list/{entry_id}/progress/', {'watched_episodes': 15}, format='json')
    assert res.status_code == 200
    print(f"Progress updated! Watched Episodes: {res.data['watched_episodes']} / {res.data['total_episodes']}")

    # Rate and add note
    print(f"\n[Step 5b] Rating entry 9/10 with note...")
    res = client.patch(f'/api/list/{entry_id}/', {'rating': 9, 'note': 'Intense battle of wits.'}, format='json')
    assert res.status_code == 200
    print(f"Entry updated! Rating: {res.data['rating']}/10, Note: '{res.data['note']}'")

    # Step 6: View dashboard statistics calculated from database records
    print("\n[Step 6] Viewing Dashboard statistics calculated directly from database records...")
    res = client.get('/api/dashboard/')
    assert res.status_code == 200
    stats = res.data['stats']
    print(f"Live Dashboard Stats: {json.dumps(stats, indent=2)}")
    assert stats['total_episodes_watched'] == 15
    assert stats['average_rating'] == 9.0
    print("Verification: Dashboard stats strictly match database state.")

    # Step 7: Send progress query message to RYUK
    print("\n[Step 7a] Asking RYUK: 'Summarize my progress'...")
    res = client.post('/api/ryuk/messages/', {'message': 'Summarize my progress'}, format='json')
    assert res.status_code == 201
    print(f"RYUK Reply:\n{res.data['reply']}")

    # Step 7b: Send AI query to RYUK (demonstrating graceful fallback when AI key is unconfigured)
    print("\n[Step 7b] Asking RYUK for recommendation (with AI key unconfigured)...")
    res = client.post('/api/ryuk/messages/', {'message': 'What should I watch next?'}, format='json')
    assert res.status_code == 503
    print(f"Status Code: 503 (Unavailable)")
    print(f"Error Code: {res.data['error']}")
    print(f"Fallback Notice: {res.data['message']}")
    print(f"Discovery suggestions offered: {len(res.data['suggestions'])} items")
    for s in res.data['suggestions']:
        print(f" - Suggestion: {s['title']} (MAL: {s['mal_id']})")

    # Step 8: Test invalid input error format
    print("\n[Step 8] Testing standardized error format on invalid input (query length < 2)...")
    res = client.get('/api/anime/search/?q=x')
    assert res.status_code == 400
    print(f"Status: {res.status_code}")
    print(f"Error Envelope: {json.dumps(res.data, indent=2)}")

    print("\n" + "=" * 70)
    print("ALL 7 CORE WORKFLOW STEPS DEMONSTRATED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    run_demonstration()
