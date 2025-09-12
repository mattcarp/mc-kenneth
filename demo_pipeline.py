#!/usr/bin/env python3
"""
Demo of ElevenLabs Audio Processing Pipeline
Shows the complete preprocessing → API workflow
"""

import sys
import os
import numpy as np
import soundfile as sf
from pathlib import Path
import tempfile

sys.path.insert(0, 'src')
from audio_preprocessor import AudioPreprocessor
from elevenlabs_rf_processor import ElevenLabsRFProcessor

def create_demo_rf_audio():
    """Create realistic RF audio simulation"""
    duration = 8.0
    sample_rate = 22050  # Different sample rate to test conversion
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Simulate voice transmission with realistic RF characteristics
    voice_freq = 180  # Lower fundamental for male voice
    voice = (np.sin(2 * np.pi * voice_freq * t) * 0.4 +
             np.sin(2 * np.pi * voice_freq * 2.1 * t) * 0.25 +  # Slightly off-harmonic
             np.sin(2 * np.pi * voice_freq * 3.2 * t) * 0.15)
    
    # Add realistic voice characteristics
    voice *= (1 + 0.6 * np.sin(2 * np.pi * 2.5 * t))  # Vibrato
    voice *= np.exp(-0.1 * np.abs(np.sin(2 * np.pi * 0.5 * t)))  # Amplitude variation
    
    # RF-specific noise characteristics
    # White noise (atmospheric)
    white_noise = np.random.normal(0, 0.3, len(t))
    
    # Pink noise (1/f noise common in RF)
    pink_noise = np.cumsum(np.random.normal(0, 0.2, len(t)))
    pink_noise = pink_noise / np.std(pink_noise) * 0.25
    
    # Intermittent interference
    for i in range(0, int(duration), 2):
        start_idx = int(i * sample_rate)
        burst_length = int(0.3 * sample_rate)
        if i % 4 == 0:  # Every 4 seconds
            interference = np.sin(2 * np.pi * 1500 * t[start_idx:start_idx + burst_length]) * 0.5
            white_noise[start_idx:start_idx + burst_length] += interference
    
    # Combine all components
    rf_audio = voice + white_noise + pink_noise
    
    # Simulate analog transmission distortion
    rf_audio = np.tanh(rf_audio * 1.2) * 0.9  # Soft saturation
    
    return rf_audio, sample_rate

def main():
    """Demonstrate the complete pipeline"""
    print("🎙️  ElevenLabs RF Audio Processing Demo")
    print("=" * 50)
    
    # Create realistic RF audio
    print("📡 Creating simulated RF audio capture...")
    rf_audio, sample_rate = create_demo_rf_audio()
    print(f"   Duration: {len(rf_audio)/sample_rate:.1f}s @ {sample_rate}Hz")
    print(f"   Contains: Voice + White noise + Pink noise + RF interference")
    
    # Save original
    with tempfile.NamedTemporaryFile(suffix='_original.wav', delete=False) as tmp:
        sf.write(tmp.name, rf_audio, sample_rate)
        original_file = Path(tmp.name)
    
    print(f"   Saved original: {original_file.name}")
    
    # Test preprocessor only (no API key needed)
    print("\n🔧 Testing Audio Preprocessor...")
    preprocessor = AudioPreprocessor()
    
    try:
        processed_file = preprocessor.process_file(original_file)
        
        # Load and analyze processed audio
        processed_audio, processed_sr = sf.read(processed_file)
        
        print("✅ Preprocessing successful!")
        print(f"   Sample rate: {sample_rate}Hz → {processed_sr}Hz")
        print(f"   Duration: {len(rf_audio)/sample_rate:.2f}s → {len(processed_audio)/processed_sr:.2f}s")
        print(f"   Format: {processed_audio.dtype}")
        print(f"   RMS level: {np.sqrt(np.mean(processed_audio**2)):.4f}")
        
        # Demonstrate streaming processing
        print("\n📊 Testing Streaming Mode...")
        chunk_duration = 1.0  # 1 second chunks
        chunk_samples = int(sample_rate * chunk_duration)
        
        chunks_processed = 0
        for start in range(0, len(rf_audio), chunk_samples):
            chunk = rf_audio[start:start + chunk_samples]
            if len(chunk) > chunk_samples // 2:  # Skip tiny end chunks
                processed_chunk = preprocessor.process_stream_chunk(chunk, sample_rate)
                chunks_processed += 1
        
        print(f"✅ Processed {chunks_processed} streaming chunks")
        
        # API demonstration (would need key)
        print("\n🔑 ElevenLabs API Integration Status:")
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if api_key:
            print("   ✅ API key available - ready for voice isolation")
            print("   Next: Would send preprocessed audio to ElevenLabs")
            print("   Expected: Clean voice output with noise removed")
        else:
            print("   ⚠️  No API key - preprocessor ready for integration")
            print("   To test full pipeline: export ELEVENLABS_API_KEY='your_key'")
        
        # Cleanup
        original_file.unlink()
        processed_file.unlink()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"   Pipeline stages: RF Audio → Preprocessor → [ElevenLabs] → Clean Audio")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        original_file.unlink()

if __name__ == "__main__":
    main()