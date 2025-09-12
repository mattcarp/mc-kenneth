#!/usr/bin/env python3
"""Test ElevenLabs API response more carefully"""

from dotenv import load_dotenv
load_dotenv()
import os
import requests
from pathlib import Path
import soundfile as sf
import numpy as np

api_key = os.getenv('ELEVENLABS_API_KEY')
print(f"API Key loaded: {'Yes' if api_key else 'No'}")

# Read original file
original_file = Path("REAL_RTL_CAPTURE_FM_Radio_Test_88.5MHz_20250912_194650.wav")
audio_data, sample_rate = sf.read(str(original_file))
print(f"\nOriginal file: {original_file.name}")
print(f"Duration: {len(audio_data)/sample_rate:.1f}s")
print(f"Sample rate: {sample_rate} Hz")

# Prepare for API
audio_16bit = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
import io
buffer = io.BytesIO()
sf.write(buffer, audio_16bit, sample_rate, format='WAV')
buffer.seek(0)
audio_bytes = buffer.read()

print(f"\nSending {len(audio_bytes)} bytes to ElevenLabs...")

# Make API request with detailed response checking
url = "https://api.elevenlabs.io/v1/audio-isolation"
headers = {"xi-api-key": api_key}
files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}

response = requests.post(url, headers=headers, files=files, timeout=120)

print(f"\nAPI Response:")
print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Content-Type: {response.headers.get('content-type')}")
print(f"Response size: {len(response.content)} bytes")

if response.status_code == 200:
    # Save the response for inspection
    test_output = Path("test_api_response.mp3")
    with open(test_output, 'wb') as f:
        f.write(response.content)
    print(f"\nSaved response to: {test_output}")
    
    # Check if it's actually audio or an error message
    if 'audio' in response.headers.get('content-type', '').lower():
        print("✅ Response appears to be audio")
    else:
        print("⚠️ Response might not be audio")
        # Try to decode as text in case it's an error
        try:
            text = response.content[:500].decode('utf-8', errors='ignore')
            print(f"First 500 bytes as text: {text}")
        except:
            pass
else:
    print(f"❌ Error: {response.text}")
