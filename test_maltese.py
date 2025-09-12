#!/usr/bin/env python3
"""
Test 2: Maltese speech capture
"""

from dotenv import load_dotenv
load_dotenv()
import os
import requests
from pathlib import Path
import soundfile as sf
import numpy as np
import subprocess
import time

api_key = os.getenv('ELEVENLABS_API_KEY')

# Test with Maltese speech
original_file = Path("capture_100_2MHz.wav")
print("\n📻 Test 2: Maltese Speech")
print("=" * 60)
print(f"ORIGINAL FILE: {original_file.name}")
print("Content: Clear Maltese speech\n")

# Read original
audio_data, sample_rate = sf.read(str(original_file))

# Prepare for API
audio_16bit = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
import io
buffer = io.BytesIO()
sf.write(buffer, audio_16bit, sample_rate, format='WAV')
buffer.seek(0)
audio_bytes = buffer.read()

# Send to ElevenLabs
print("📡 Sending to ElevenLabs...")
url = "https://api.elevenlabs.io/v1/audio-isolation"
headers = {"xi-api-key": api_key}
files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}
data = {"file_format": "other"}

response = requests.post(url, headers=headers, files=files, data=data, timeout=60)

if response.status_code == 200:
    isolated_file = Path("100_2MHz_AFTER_elevenlabs.mp3")
    with open(isolated_file, 'wb') as f:
        f.write(response.content)
    
    # Play BEFORE
    print(f"\n🔊 PLAYING BEFORE (Original Maltese speech):")
    print(f"   File: {original_file.name}")
    subprocess.run(f"afplay {original_file}", shell=True)
    
    time.sleep(1)
    
    # Play AFTER
    print(f"\n🔊 PLAYING AFTER (ElevenLabs 'isolated'):")
    print(f"   File: {isolated_file.name}")
    subprocess.run(f"afplay {isolated_file}", shell=True)
