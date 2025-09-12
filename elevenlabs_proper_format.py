#!/usr/bin/env python3
"""
PROPER ElevenLabs implementation with correct audio format
Converting to exact specification: 16-bit PCM, 16kHz, mono, little-endian
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

api_key = os.getenv('ELEVENLABS_API_KEY')

def convert_to_elevenlabs_format(audio_file):
    """Convert audio to ElevenLabs optimal format: 16-bit PCM, 16kHz, mono"""
    
    # Read original audio
    audio_data, orig_sr = sf.read(str(audio_file))
    
    print(f"  Original: {orig_sr} Hz, shape: {audio_data.shape}")
    
    # Ensure mono (if stereo, take first channel or average)
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]  # Take first channel
    
    # Resample to EXACTLY 16000 Hz
    audio_16khz = librosa.resample(audio_data, orig_sr=orig_sr, target_sr=16000)
    
    # Convert to 16-bit PCM (little-endian is default on most systems)
    audio_16bit = np.clip(audio_16khz * 32767, -32768, 32767).astype(np.int16)
    
    print(f"  Converted: 16000 Hz, {len(audio_16bit)} samples, 16-bit PCM")
    
    # Return raw PCM bytes (no WAV header for pcm_s16le_16 format)
    return audio_16bit.tobytes()

def test_with_proper_format(audio_file, description):
    """Test ElevenLabs with properly formatted audio"""
    
    print(f"\n📻 Testing: {audio_file}")
    print(f"Description: {description}")
    print("-" * 60)
    
    # Convert to exact format
    print("Converting to ElevenLabs format...")
    pcm_bytes = convert_to_elevenlabs_format(audio_file)
    
    # Send to API with correct format specification
    print("📡 Sending to ElevenLabs (pcm_s16le_16 format)...")
    
    url = "https://api.elevenlabs.io/v1/audio-isolation"
    headers = {"xi-api-key": api_key}
    
    # For PCM format, send raw bytes
    files = {"audio": ("audio.pcm", pcm_bytes, "audio/pcm")}
    data = {"file_format": "pcm_s16le_16"}  # SPECIFY EXACT FORMAT!
    
    response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    
    if response.status_code == 200:
        # Save result
        output_name = f"{Path(audio_file).stem}_PROPER_elevenlabs.mp3"
        output_file = Path(output_name)
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Saved: {output_name}")
        print(f"   Size: {len(response.content)} bytes")
        
        # Play BEFORE
        print(f"\n🔊 PLAYING BEFORE: {audio_file}")
        subprocess.run(f"afplay {audio_file}", shell=True)
        
        # Play AFTER
        print(f"\n🔊 PLAYING AFTER: {output_name}")
        subprocess.run(f"afplay {output_file}", shell=True)
        
        return output_file
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        return None

# Test with our best captures
print("🎯 ElevenLabs with PROPER Format (16-bit PCM @ 16kHz)")
print("=" * 60)

# Test 1: Italian radio
test_with_proper_format(
    "capture_91_1MHz.wav",
    "Italian speech + music, low noise"
)
