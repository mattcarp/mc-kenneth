#!/usr/bin/env python3
"""
Quick Voice Activity Scanner
Scans maritime/aviation frequencies for active voice communications
"""

import subprocess
import time
import numpy as np
from pathlib import Path

class VoiceActivityScanner:
    """Quickly scan frequencies to find active voice communications"""
    
    def __init__(self):
        self.maritime_freqs = {
            'Channel 16 (Emergency)': 156.800e6,
            'Channel 09 (Calling)': 156.450e6, 
            'Channel 13 (Bridge)': 156.650e6,
            'Channel 22A (CG)': 157.100e6,
        }
        
        self.aviation_freqs = {
            'Emergency (121.5)': 121.500e6,
            'ATC Primary': 118.100e6,
            'Approach': 119.100e6, 
            'Ground': 121.900e6,
            'Tower': 120.900e6,
        }
    
    def quick_sample(self, frequency, duration=5):
        """Take a quick 5-second sample to check for voice activity"""
        freq_mhz = frequency / 1e6
        
        print(f"📡 Sampling {freq_mhz:.3f} MHz for {duration}s...")
        
        # Quick capture command
        cmd = [
            'timeout', str(duration + 2),  # Add 2s timeout buffer
            'rx_sdr',
            '-d', 'driver=sdrplay',
            '-s', '250000',  # 250kHz bandwidth
            '-f', str(int(frequency)),
            '-g', '40',
            '-n', str(int(250000 * duration)),
            f'/tmp/quick_sample_{freq_mhz:.3f}.iq'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=duration + 5)
            if result.returncode == 0:
                # Quick analysis of captured IQ data
                iq_file = f'/tmp/quick_sample_{freq_mhz:.3f}.iq'
                return self.analyze_voice_activity(iq_file, freq_mhz)
            else:
                print(f"   ❌ Capture failed")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def analyze_voice_activity(self, iq_file, freq_mhz):
        """Analyze IQ data for voice-like activity"""
        try:
            # Load IQ samples
            iq_data = np.fromfile(iq_file, dtype=np.complex64)
            
            if len(iq_data) < 1000:
                print(f"   📊 {freq_mhz:.3f} MHz: No signal")
                return False
            
            # Simple FM demodulation
            phase = np.unwrap(np.angle(iq_data))
            audio = np.diff(phase)
            
            # Voice activity indicators
            rms = np.sqrt(np.mean(audio**2))
            peak = np.max(np.abs(audio))
            
            # Simple voice detection heuristics
            dynamic_range = peak / (rms + 1e-10)
            
            # Clean up temp file
            Path(iq_file).unlink()
            
            # Voice activity thresholds
            if rms > 0.1 and dynamic_range > 5:
                print(f"   🎙️  {freq_mhz:.3f} MHz: VOICE DETECTED (RMS: {rms:.3f}, DR: {dynamic_range:.1f})")
                return True
            elif rms > 0.05:
                print(f"   📻 {freq_mhz:.3f} MHz: Signal present (RMS: {rms:.3f})")
                return False
            else:
                print(f"   📊 {freq_mhz:.3f} MHz: Quiet (RMS: {rms:.3f})")
                return False
                
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            return False
    
    def scan_for_voices(self):
        """Scan all frequencies to find active voice communications"""
        print("🔍 Scanning for Active Voice Communications...")
        print("=" * 60)
        
        active_freqs = []
        
        print("\n🚢 Maritime Frequencies:")
        for name, freq in self.maritime_freqs.items():
            if self.quick_sample(freq):
                active_freqs.append(('Maritime', name, freq))
            time.sleep(1)  # Brief pause between scans
        
        print("\n✈️  Aviation Frequencies:")  
        for name, freq in self.aviation_freqs.items():
            if self.quick_sample(freq):
                active_freqs.append(('Aviation', name, freq))
            time.sleep(1)
        
        print(f"\n🎯 Voice Activity Summary:")
        print("=" * 40)
        
        if active_freqs:
            for category, name, freq in active_freqs:
                print(f"✅ {category} {name}: {freq/1e6:.3f} MHz")
            
            print(f"\n📝 Recommendation:")
            print(f"   Capture from these {len(active_freqs)} active frequencies")
            print(f"   Use 20-30 second captures to get complete conversations")
            
        else:
            print("❌ No voice activity detected")
            print("   Try again later or check antenna connection")
            print("   Maritime/aviation activity varies by time of day")
            
        return active_freqs

def main():
    """Quick voice activity scan"""
    scanner = VoiceActivityScanner()
    
    print("🎯 Quick Voice Activity Scanner")
    print("   Finding active maritime/aviation communications")
    print("=" * 60)
    
    # Test SDRplay connection first
    try:
        result = subprocess.run(['SoapySDRUtil', '--find'], 
                              capture_output=True, text=True, timeout=10)
        if 'sdrplay' not in result.stdout.lower():
            print("❌ SDRplay not detected via SoapySDR")
            print("Please connect SDRplay and install drivers")
            return False
    except Exception as e:
        print(f"❌ SoapySDR test failed: {e}")
        return False
    
    print("✅ SDRplay detected, starting voice scan...\n")
    
    # Scan for active voices
    active_frequencies = scanner.scan_for_voices()
    
    if active_frequencies:
        print(f"\n🎙️  Ready for voice capture!")
        print(f"   Run: python3 maritime_aviation_capture.py")
        print(f"   Focus on the {len(active_frequencies)} active frequencies above")
    
    return True

if __name__ == "__main__":
    main()