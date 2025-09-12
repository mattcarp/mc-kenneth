#!/usr/bin/env python3
"""
FM Signal Capture and Audio Conversion for Malta
Works around macOS audio issues by saving to WAV file
"""

import subprocess
import numpy as np
import scipy.signal as signal
from scipy.io import wavfile
import os
import sys

def capture_fm_signal(freq_mhz=103.7, duration=10):
    """Capture FM signal from HackRF"""
    print(f"\n🎯 CAPTURING FM SIGNAL: {freq_mhz} MHz")
    print(f"📻 Station: Magic Malta (strongest in Gozo)")
    print(f"⏱️  Duration: {duration} seconds")
    
    freq_hz = int(freq_mhz * 1e6)
    sample_rate = 2000000  # 2 MHz sample rate
    capture_file = "/tmp/fm_capture.iq"
    
    # Capture IQ data
    cmd = [
        "hackrf_transfer",
        "-r", capture_file,
        "-f", str(freq_hz),
        "-s", str(sample_rate),
        "-a", "1",  # Amplifier on
        "-l", "32",  # LNA gain
        "-g", "40",  # VGA gain
        "-n", str(sample_rate * duration)  # Number of samples
    ]
    
    print("\n📡 Capturing signal...")
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=duration+5)
        print("✅ Signal captured!")
    except subprocess.TimeoutExpired:
        print("✅ Capture complete (timeout expected)")
    except Exception as e:
        print(f"❌ Capture failed: {e}")
        return False, 0
    
    return capture_file, sample_rate

def demodulate_fm(iq_file, sample_rate):
    """Demodulate FM signal to audio"""
    print("\n🔊 Demodulating FM signal...")
    
    # Read IQ data
    with open(iq_file, 'rb') as f:
        raw_data = f.read()
    
    # Convert to complex IQ samples
    iq_data = np.frombuffer(raw_data, dtype=np.int8)
    iq_data = iq_data[0::2] + 1j * iq_data[1::2]
    iq_data = iq_data.astype(np.float32) / 128.0
    
    print(f"📊 Loaded {len(iq_data)} samples")
    
    # FM demodulation using phase difference
    phase = np.angle(iq_data)
    demod = np.diff(np.unwrap(phase))
    
    # Normalize
    demod = demod / np.max(np.abs(demod))
    
    # Decimate to audio rate (48 kHz)
    audio_rate = 48000
    decimation = int(sample_rate / audio_rate)
    audio = signal.decimate(demod, decimation)
    
    # Apply de-emphasis filter (50 µs for Europe)
    tau = 50e-6
    b, a = signal.bilinear([tau], [tau, 1], fs=audio_rate)
    audio = signal.lfilter(b, a, audio)
    
    # Normalize and convert to 16-bit
    audio = audio * 0.8  # Prevent clipping
    audio = np.clip(audio, -1, 1)
    audio = (audio * 32767).astype(np.int16)
    
    # Save as WAV
    output_file = "/tmp/fm_audio.wav"
    wavfile.write(output_file, audio_rate, audio)
    
    print(f"✅ Audio saved to: {output_file}")
    print(f"📻 Audio duration: {len(audio)/audio_rate:.1f} seconds")
    
    return output_file

def play_audio(wav_file):
    """Play the audio file"""
    print("\n🎵 Playing demodulated audio...")
    
    # Try different audio players
    players = [
        ["afplay", wav_file],  # macOS native
        ["open", wav_file],    # Opens in default app
        ["sox", wav_file, "-d"],  # SoX play
    ]
    
    for cmd in players:
        try:
            print(f"   Trying: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("✅ Audio played successfully!")
            return True
        except:
            continue
    
    print(f"\n📁 Audio file saved but couldn't auto-play.")
    print(f"   Open manually: {wav_file}")
    return False

def main():
    print("="*60)
    print("   🎭 MALTA FM RADIO RECEIVER")
    print("   📍 Location: Victoria, Gozo")
    print("   📻 Target: Magic Malta 103.7 MHz")
    print("="*60)
    
    # Check for HackRF
    try:
        subprocess.run(["hackrf_info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("✅ HackRF detected!")
    except:
        print("❌ HackRF not found! Is it connected?")
        sys.exit(1)
    
    # Capture signal
    iq_file, sample_rate = capture_fm_signal(freq_mhz=103.7, duration=10)
    
    if iq_file and iq_file != False and os.path.exists(iq_file):
        # Demodulate
        wav_file = demodulate_fm(iq_file, sample_rate)
        
        # Play audio
        play_audio(wav_file)
        
        print("\n🎉 Done! If you heard music, we're in business!")
        print("   If not, try opening: /tmp/fm_audio.wav")
    else:
        print("❌ Failed to capture signal")

if __name__ == "__main__":
    main()
