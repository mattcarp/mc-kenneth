#!/usr/bin/env python3
"""
Test ElevenLabs consistency with file_format parameter
"""

from dotenv import load_dotenv
load_dotenv()
import os
import requests
from pathlib import Path
import soundfile as sf
import hashlib

api_key = os.getenv('ELEVENLABS_API_KEY')

# Use the same good Italian capture
test_file = Path("capture_91_1MHz.wav")
audio_data, sample_rate = sf.read(str(test_file))

# Prepare audio (keep at original sample rate)
import numpy as np
audio_16bit = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)

import io
buffer = io.BytesIO()
sf.write(buffer, audio_16bit, sample_rate, format='WAV')
buffer.seek(0)
audio_bytes = buffer.read()

print(f"Testing same file 3 times WITH file_format parameter")
print(f"Input MD5: {hashlib.md5(audio_bytes).hexdigest()}\n")

url = "https://api.elevenlabs.io/v1/audio-isolation"
headers = {"xi-api-key": api_key}

results = []
for i in range(3):
    files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}
    data = {"file_format": "other"}
    
    response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    
    md5 = hashlib.md5(response.content).hexdigest()
    results.append({
        'attempt': i+1,
        'size': len(response.content),
        'md5': md5
    })
    
    print(f"Attempt {i+1}: Size={len(response.content)}, MD5={md5}")

print("\n=== RESULTS ===")
if len(set(r['md5'] for r in results)) == 1:
    print("✅ CONSISTENT: All responses are identical!")
else:
    print("❌ INCONSISTENT: Still getting different outputs for same input")
