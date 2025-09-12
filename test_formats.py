#!/usr/bin/env python3
"""
Try with WAV container but 16kHz sample rate
"""

from dotenv import load_dotenv
load_dotenv()
import os
import requests
from pathlib import Path
import soundfile as sf
import numpy as np
import subprocess
import librosa
import io

api_key = os.getenv('ELEVENLABS_API_KEY')

audio_file = Path("capture_91_1MHz.wav")

# Read and convert
audio_data, orig_sr = sf.read(str(audio_file))
print(f"Original: {orig_sr} Hz")

# Resample to 16kHz
audio_16khz = librosa.resample(audio_data, orig_sr=orig_sr, target_sr=16000)

# Convert to 16-bit
audio_16bit = np.clip(audio_16khz * 32767, -32768, 32767).astype(np.int16)

# Create WAV in memory at 16kHz
buffer = io.BytesIO()
sf.write(buffer, audio_16bit, 16000, format='WAV', subtype='PCM_16')
buffer.seek(0)
wav_bytes = buffer.read()

print(f"Converted: 16kHz WAV, {len(wav_bytes)} bytes")

# Try both format options
for format_option in ["pcm_s16le_16", "other"]:
    print(f"\n📡 Testing with file_format='{format_option}'...")
    
    url = "https://api.elevenlabs.io/v1/audio-isolation"
    headers = {"xi-api-key": api_key}
    files = {"audio": ("audio.wav", wav_bytes, "audio/wav")}
    data = {"file_format": format_option}
    
    response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        output = f"test_16khz_{format_option}.mp3"
        with open(output, 'wb') as f:
            f.write(response.content)
        print(f"✅ Success! Saved: {output}")
        print(f"Size: {len(response.content)} bytes")
        
        print(f"\n🔊 PLAYING RESULT from {format_option}:")
        subprocess.run(f"afplay {output}", shell=True)
    else:
        print(f"❌ Error: {response.text}")
