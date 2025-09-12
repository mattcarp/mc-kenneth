#!/usr/bin/env python3
"""
Proper before/after comparison for ElevenLabs isolation
Clear file naming and side-by-side playback
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

# Test with our best capture - 91.1 MHz Italian with low noise
original_file = Path("capture_91_1MHz.wav")
print("📻 Testing ElevenLabs Audio Isolation")
print("=" * 60)
print(f"ORIGINAL FILE: {original_file.name}")
print("Content: Italian speech with music, LOW NOISE, good quality\n")

# Read original
audio_data, sample_rate = sf.read(str(original_file))
duration = len(audio_data) / sample_rate
print(f"Duration: {duration:.1f} seconds")
print(f"Sample rate: {sample_rate} Hz\n")

# Prepare for API
audio_16bit = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
import io
buffer = io.BytesIO()
sf.write(buffer, audio_16bit, sample_rate, format='WAV')
buffer.seek(0)
audio_bytes = buffer.read()

# Send to ElevenLabs
print("📡 Sending to ElevenLabs API...")
url = "https://api.elevenlabs.io/v1/audio-isolation"
headers = {"xi-api-key": api_key}
files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}
data = {"file_format": "other"}

response = requests.post(url, headers=headers, files=files, data=data, timeout=60)

if response.status_code == 200:
    # Save with clear naming
    isolated_file = Path("91_1MHz_AFTER_elevenlabs.mp3")
    with open(isolated_file, 'wb') as f:
        f.write(response.content)
    print(f"✅ Saved: {isolated_file.name}\n")
    
    # Play BEFORE
    print("🔊 PLAYING BEFORE (Original Italian radio):")
    print(f"   File: {original_file.name}")
    subprocess.run(f"afplay {original_file}", shell=True)
    
    time.sleep(1)
    
    # Play AFTER
    print("\n🔊 PLAYING AFTER (ElevenLabs 'isolated'):")
    print(f"   File: {isolated_file.name}")
    subprocess.run(f"afplay {isolated_file}", shell=True)
    
    print("\n❓ Does the AFTER file:")
    print("   - Sound like isolated Italian speech from the radio?")
    print("   - Sound completely different/unrelated?")
    print("   - Have any relation to the original content?")
else:
    print(f"❌ API Error: {response.status_code}")
