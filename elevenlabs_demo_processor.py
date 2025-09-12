#!/usr/bin/env python3
"""
ElevenLabs Demo Processor - Process top voice samples to demonstrate isolation
"""

import os
import sys
import soundfile as sf
import requests
import time
from pathlib import Path

class ElevenLabsDemo:
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            print("❌ ELEVENLABS_API_KEY environment variable not set")
            sys.exit(1)
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.capture_dir = Path("rf_captures/autonomous_hunt_20250911_212457")
        self.output_dir = Path("elevenlabs_processed")
        self.output_dir.mkdir(exist_ok=True)
        
    def process_file(self, audio_file):
        """Process a single audio file through ElevenLabs Voice Isolation"""
        
        print(f"🎵 Processing: {audio_file.name}")
        
        # Read audio file
        try:
            audio_data, sample_rate = sf.read(str(audio_file))
            
            # Convert to bytes for API
            import io
            import numpy as np
            
            # Ensure proper format (16-bit PCM)
            audio_16bit = (audio_data * 32767).astype(np.int16)
            
            # Create WAV file in memory
            buffer = io.BytesIO()
            sf.write(buffer, audio_16bit, sample_rate, format='WAV')
            buffer.seek(0)
            audio_bytes = buffer.read()
            
        except Exception as e:
            print(f"   ❌ Error reading audio: {e}")
            return None
        
        # Prepare API request
        url = f"{self.base_url}/audio-isolation"
        headers = {
            "xi-api-key": self.api_key
        }
        
        files = {
            "audio": ("audio.wav", audio_bytes, "audio/wav")
        }
        
        try:
            print(f"   🚀 Sending to ElevenLabs API...")
            response = requests.post(url, headers=headers, files=files, timeout=60)
            
            if response.status_code == 200:
                # Save processed audio
                output_file = self.output_dir / f"isolated_{audio_file.name}"
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                print(f"   ✅ Processed successfully → {output_file}")
                return output_file
            else:
                print(f"   ❌ API Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Request error: {e}")
            return None
    
    def process_demo_batch(self, num_files=5):
        """Process first few files from batch 1 for demo"""
        
        print("🎯 ElevenLabs Voice Isolation Demo")
        print("=" * 50)
        
        # Load batch 1 files
        batch_file = "elevenlabs_batch_01.txt"
        if not Path(batch_file).exists():
            print("❌ Batch file not found")
            return
        
        with open(batch_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() 
                    if not line.startswith('#') and line.strip()]
        
        print(f"📦 Processing first {num_files} files from Batch 1...")
        
        processed_count = 0
        
        for filename in lines[:num_files]:
            audio_file = self.capture_dir / filename
            
            if not audio_file.exists():
                print(f"   ⚠️  File not found: {filename}")
                continue
            
            result = self.process_file(audio_file)
            if result:
                processed_count += 1
            
            # Rate limiting
            time.sleep(2)
        
        print(f"\n🎉 Demo complete! Processed {processed_count}/{num_files} files")
        print(f"📁 Processed files saved to: {self.output_dir}")
        
        # List processed files
        processed_files = list(self.output_dir.glob("*.wav"))
        if processed_files:
            print("\n📊 Processed Files:")
            for f in processed_files:
                size_mb = f.stat().st_size / (1024*1024)
                print(f"   • {f.name} ({size_mb:.1f}MB)")

def main():
    processor = ElevenLabsDemo()
    processor.process_demo_batch(3)  # Start with just 3 files for demo

if __name__ == "__main__":
    main()