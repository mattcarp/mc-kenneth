#!/usr/bin/env python3
"""Test if API returns different content for the same input"""

from dotenv import load_dotenv
load_dotenv()
import os
import requests
from pathlib import Path
import soundfile as sf
import numpy as np
import hashlib

api_key = os.getenv('ELEVENLABS_API_KEY')

# Use the same file every time
test_file = Path("REAL_RTL_CAPTURE_FM_Radio_Test_88.5MHz_20250912_194650.wav")
audio_data, sample_rate = sf.read(str(test_file))

# Prepare the EXACT same audio bytes
audio_16bit = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
import io
buffer = io.BytesIO()
sf.write(buffer, audio_16bit, sample_rate, format='WAV')
buffer.seek(0)
audio_bytes = buffer.read()

print(f"Testing with SAME file 3 times: {test_file.name}")
print(f"Input file MD5: {hashlib.md5(audio_bytes).hexdigest()}\n")

url = "https://api.elevenlabs.io/v1/audio-isolation"
headers = {"xi-api-key": api_key}

results = []
for i in range(3):
    print(f"Attempt {i+1}:")
    files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}
    response = requests.post(url, headers=headers, files=files, timeout=120)
    
    md5 = hashlib.md5(response.content).hexdigest()
    results.append({
        'attempt': i+1,
        'status': response.status_code,
        'size': len(response.content),
        'md5': md5
    })
    
    # Save each response
    output = Path(f"test_same_input_{i+1}.mp3")
    with open(output, 'wb') as f:
        f.write(response.content)
    
    print(f"  Status: {response.status_code}")
    print(f"  Size: {len(response.content)} bytes")
    print(f"  MD5: {md5}")
    print(f"  Saved to: {output}\n")

print("\n=== COMPARISON ===")
print("Same input file, 3 API calls:")
for r in results:
    print(f"Attempt {r['attempt']}: Size={r['size']}, MD5={r['md5']}")

if len(set(r['md5'] for r in results)) == 1:
    print("\n✅ All responses are IDENTICAL (same MD5)")
else:
    print("\n❌ Responses are DIFFERENT despite same input!")
    print("This means the API is generating/hallucinating different content each time!")
