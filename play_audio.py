#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

def play_audio(file_path):
    try:
        # Try different audio players
        players = ['afplay', 'play', 'aplay', 'paplay']
        for player in players:
            try:
                subprocess.run([player, str(file_path)], check=True, 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"🔊 Playing: {file_path.name}")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        print("❌ No audio player found. Install sox or use system audio player.")
        return False
    except Exception as e:
        print(f"❌ Audio playback failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 play_audio.py <audio_file.wav>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    play_audio(file_path)
