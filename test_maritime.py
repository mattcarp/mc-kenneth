#!/usr/bin/env python3
"""Test with different RF capture"""

from dotenv import load_dotenv
load_dotenv()
import os
import requests
from pathlib import Path
import soundfile as sf
import numpy as np

api_key = os.getenv('ELEVENLABS_API_KEY')

# Try Maritime CH16 this time
test_file = Path("REAL_RTL_CAPTURE_Maritime_CH16_156.8MHz_20250912_194656.wav")
print(f"Testing with: {test_file.name}")

audio_data, sample_rate = sf.read(str(test_file))
print(f"Duration: {len(audio_data)/sample_rate:.1f}s, Sample rate: {sample_rate} Hz")

# Prepare for API
audio_16bit = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
import io
buffer = io.BytesIO()
sf.write(buffer, audio_16bit, sample_rate, format='WAV')
buffer.seek(0)
audio_bytes = buffer.read()

print(f"Sending to ElevenLabs...")

# API request
url = "https://api.elevenlabs.io/v1/audio-isolation"
headers = {"xi-api-key": api_key}
files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}

response = requests.post(url, headers=headers, files=files, timeout=120)

print(f"Status: {response.status_code}")
print(f"Response size: {len(response.content)} bytes")

if response.status_code == 200:
    output = Path("test_maritime_isolated.mp3")
    with open(output, 'wb') as f:
        f.write(response.content)
    print(f"Saved to: {output}")
