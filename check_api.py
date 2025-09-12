#!/usr/bin/env python3
"""Check what the API is actually returning"""

from dotenv import load_dotenv
load_dotenv()
import os
import requests

api_key = os.getenv('ELEVENLABS_API_KEY')

# First, let's check if we can access the API at all
print("Testing ElevenLabs API access...")
print(f"API Key: {api_key[:10]}..." if api_key else "No key")

# Try to get user info or verify the API key works
url = "https://api.elevenlabs.io/v1/user"
headers = {"xi-api-key": api_key}

response = requests.get(url, headers=headers)
print(f"\nUser endpoint status: {response.status_code}")
if response.status_code == 200:
    print("✅ API key is valid and working")
    import json
    user_data = response.json()
    print(f"User info: {json.dumps(user_data, indent=2)[:500]}...")
else:
    print(f"❌ API error: {response.text}")
