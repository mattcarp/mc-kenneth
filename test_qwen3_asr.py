#!/usr/bin/env python3
"""
Test Qwen3-ASR with Maritime Voice Samples
Using the actual voice captures from Kenneth RF project
"""

import requests
import json
import os
from pathlib import Path

def test_qwen3_asr():
    print("🎯 Testing Qwen3-ASR with Kenneth Maritime Samples")
    print("=" * 60)
    
    # Maritime voice samples
    samples = [
        "VOICE_CAPTURE_CH16_Emergency_156.800MHz_20250911_201907.wav",
        "VOICE_CAPTURE_CH09_Calling_156.450MHz_20250911_202004.wav",
        "YOLO_REALISTIC_MARITIME_20250911_212141.wav"
    ]
    
    # Maritime context for enhanced recognition
    maritime_context = """
    Maritime VHF Radio Communications Context:
    
    CHANNEL 16 (156.800 MHz) - International Distress and Calling
    CHANNEL 09 (156.450 MHz) - Commercial/Recreational Calling
    
    Common Maritime Terms:
    - MAYDAY: Life-threatening emergency
    - PAN-PAN: Urgent safety message  
    - SÉCURITÉ: Safety message
    - Over: End of transmission, expecting reply
    - Out: End of conversation
    - Roger: Message received and understood
    - Wilco: Will comply
    - Coast Guard: Maritime rescue service
    - Vessel Traffic Service (VTS)
    - Position reports (latitude/longitude)
    - Course and speed
    - ETA (Estimated Time of Arrival)
    - POB (Persons On Board)
    - Call signs (vessel identification)
    - Malta Coast Guard
    - Mediterranean Sea
    - Gozo, Victoria
    """
    
    # Check which samples exist
    existing_samples = []
    for sample in samples:
        if Path(sample).exists():
            size = Path(sample).stat().st_size
            print(f"✅ Found: {sample} ({size:,} bytes)")
            existing_samples.append(sample)
        else:
            print(f"❌ Missing: {sample}")
    
    if not existing_samples:
        print("❌ No voice samples found!")
        return
    
    print(f"\n🔧 Testing with {len(existing_samples)} samples")
    print(f"📝 Maritime context: {len(maritime_context)} characters")
    
    # For now, let's analyze the audio files locally first
    print("\n📊 Audio File Analysis:")
    for sample in existing_samples:
        try:
            import soundfile as sf
            data, samplerate = sf.read(sample)
            duration = len(data) / samplerate
            print(f"   📡 {sample}:")
            print(f"      Duration: {duration:.2f} seconds")
            print(f"      Sample Rate: {samplerate} Hz")
            print(f"      Channels: {data.ndim}")
            print(f"      Max Amplitude: {abs(data).max():.3f}")
        except ImportError:
            print(f"   📡 {sample}: Analysis requires soundfile package")
        except Exception as e:
            print(f"   ❌ {sample}: {e}")
    
    # Prepare API test (structure only for now)
    api_payload = {
        "context": maritime_context,
        "language": "auto",
        "enable_itn": True,
        "enable_punctuation": True
    }
    
    print(f"\n🎯 Ready for Qwen3-ASR API integration!")
    print(f"   Samples ready: {len(existing_samples)}")
    print(f"   Context prepared: ✅")
    print(f"   Next: Set up API credentials and test")
    
    return existing_samples

if __name__ == "__main__":
    samples = test_qwen3_asr()
