#!/usr/bin/env python3
"""
Correct ElevenLabs Audio Isolation implementation based on official docs
"""

from dotenv import load_dotenv
load_dotenv()
import os
import requests
from pathlib import Path
import soundfile as sf
import numpy as np
import librosa

api_key = os.getenv('ELEVENLABS_API_KEY')
print(f"API Key loaded: {'Yes' if api_key else 'No'}")

# Test with one of our good captures
test_file = Path("capture_91_1MHz.wav")  # The good Italian one

if not test_file.exists():
    print(f"❌ File not found: {test_file}")
    exit(1)

print(f"\n🎯 Testing CORRECT ElevenLabs Audio Isolation API")
print(f"File: {test_file.name}")

# Read and prepare audio
audio_data, sample_rate = sf.read(str(test_file))
print(f"Original: {sample_rate} Hz, {len(audio_data)} samples")

# Convert to 16kHz mono PCM as recommended
audio_16khz = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
audio_16bit = np.clip(audio_16khz * 32767, -32768, 32767).astype(np.int16)

print(f"Converted to: 16000 Hz, {len(audio_16bit)} samples")

# Create audio file in memory
import io
buffer = io.BytesIO()
sf.write(buffer, audio_16bit, 16000, format='WAV', subtype='PCM_16')
buffer.seek(0)
audio_bytes = buffer.read()

# Correct API endpoint from docs
# The docs page shows /audio-isolation but we need the full path
url = "https://api.elevenlabs.io/v1/audio-isolation"  # This might still be correct

headers = {
    "xi-api-key": api_key
}

# Include file_format parameter as shown in docs
files = {
    "audio": ("audio.wav", audio_bytes, "audio/wav")
}
data = {
    "file_format": "other"  # or "pcm_s16le_16" if we format it correctly
}

print(f"\n📡 Sending to ElevenLabs with file_format parameter...")
response = requests.post(url, headers=headers, files=files, data=data, timeout=60)

print(f"Status: {response.status_code}")
print(f"Headers: {response.headers.get('content-type')}")

if response.status_code == 200:
    output = Path("elevenlabs_correct_test.mp3")
    with open(output, 'wb') as f:
        f.write(response.content)
    print(f"✅ Saved to: {output}")
    print(f"Size: {len(response.content)} bytes")
    
    # Play it
    import subprocess
    subprocess.run(f"afplay {output}", shell=True)
else:
    print(f"❌ Error: {response.status_code}")
    print(f"Response: {response.text}")
