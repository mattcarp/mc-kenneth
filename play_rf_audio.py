#!/usr/bin/env python3
"""
Simple Audio Player for RF Captures
Play captured audio files to hear what we actually got
"""

import subprocess
import sys
from pathlib import Path
import time

def play_audio_file(filename):
    """Play audio file using system audio player"""
    if not Path(filename).exists():
        print(f"❌ File not found: {filename}")
        return False
    
    print(f"🎵 Playing: {filename}")
    
    # Try different audio players available on macOS
    players = [
        ['afplay', filename],           # macOS built-in player
        ['play', filename],             # SoX player  
        ['mpv', filename],              # mpv player
        ['vlc', filename, '--intf', 'dummy', '--play-and-exit']  # VLC
    ]
    
    for player_cmd in players:
        try:
            print(f"   Trying: {player_cmd[0]}")
            result = subprocess.run(player_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"   ✅ Played with {player_cmd[0]}")
                return True
            else:
                print(f"   ❌ {player_cmd[0]} failed: {result.stderr[:100]}")
                
        except FileNotFoundError:
            print(f"   ❌ {player_cmd[0]} not available")
        except subprocess.TimeoutExpired:
            print(f"   ⚠️ {player_cmd[0]} timeout")
        except Exception as e:
            print(f"   ❌ {player_cmd[0]} error: {e}")
    
    print("❌ No audio players worked")
    return False

def list_audio_files():
    """List all captured audio files"""
    files = []
    
    # Look for different types of captures
    patterns = [
        "REAL_RTL_CAPTURE_*.wav",
        "REAL_CAPTURE_*.wav", 
        "VOICE_CAPTURE_*.wav",
        "*.wav"
    ]
    
    for pattern in patterns:
        files.extend(Path('.').glob(pattern))
    
    # Remove duplicates and sort
    files = sorted(list(set(files)))
    
    return files

def main():
    print("🎵 RF Audio Player")
    print("=" * 40)
    
    # Find audio files
    audio_files = list_audio_files()
    
    if not audio_files:
        print("❌ No audio files found in current directory")
        return
    
    print(f"Found {len(audio_files)} audio files:")
    
    # List files with numbers
    for i, file in enumerate(audio_files, 1):
        size = file.stat().st_size
        print(f"  {i}. {file.name} ({size:,} bytes)")
    
    # Play the most recent real captures first
    real_captures = [f for f in audio_files if "REAL_RTL_CAPTURE" in f.name]
    
    if real_captures:
        print(f"\n🎯 Playing {len(real_captures)} REAL RF captures:")
        
        for i, capture in enumerate(real_captures, 1):
            print(f"\n📡 Playing {i}/{len(real_captures)}: {capture.name}")
            
            success = play_audio_file(str(capture))
            
            if success:
                print("   🎵 Audio playback completed")
            else:
                print("   ❌ Could not play audio")
            
            if i < len(real_captures):
                print("   (Press Ctrl+C to stop, or wait for next file...)")
                time.sleep(2)
    
    else:
        print("\n⚠️ No REAL_RTL_CAPTURE files found")
        print("Playing first available audio file:")
        
        if audio_files:
            play_audio_file(str(audio_files[0]))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Audio playback stopped by user")
