#!/usr/bin/env python3
"""
Auto-scanner for SDR++ - Finds active frequencies
Controls SDR++ to automatically tune to strong signals
"""

import subprocess
import time
import numpy as np

print("="*60)
print("   🔍 AUTO-TUNER FOR SDR++")
print("="*60)
print("\nSearching for active frequencies...\n")

# Kill any stuck processes
subprocess.run("killall hackrf_transfer 2>/dev/null", shell=True)

# List of FM frequencies to check (Malta stations + common ones)
fm_freqs = [
    87.7, 88.0, 88.5, 89.0, 89.3, 89.7,  # Start of FM band
    90.0, 90.5, 91.0, 91.5, 92.0, 92.4, 92.9,
    93.3, 93.7, 94.0, 94.5, 95.0, 95.5,
    96.0, 96.1, 96.5, 97.0, 97.5, 98.0, 98.5, 98.9,
    99.0, 99.5, 100.0, 100.3, 100.5, 101.0, 101.5,
    102.0, 102.5, 103.0, 103.5, 103.7, 104.0, 104.5,
    105.0, 105.2, 105.5, 106.0, 106.5, 107.0, 107.5, 108.0
]

strongest_freq = None
strongest_power = -100

print("Scanning FM band (88-108 MHz)...")
print("-" * 40)

for freq in fm_freqs:
    # Quick capture at each frequency
    cmd = f"timeout 0.3 hackrf_transfer -r - -f {int(freq*1e6)} -s 2000000 -n 600000 -a 1 -l 24 -g 24 2>&1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Extract power level
    power = -100
    for line in result.stderr.split('\n'):
        if "average power" in line:
            try:
                power = float(line.split("average power")[1].split("dBfs")[0].strip())
            except:
                pass
    
    # Show progress
    if power > -30:
        status = "💪 STRONG!"
        print(f"{freq:6.1f} MHz: {power:+6.1f} dBfs  {status}")
        if power > strongest_power:
            strongest_power = power
            strongest_freq = freq
    elif power > -50:
        status = "📡 Good"
        print(f"{freq:6.1f} MHz: {power:+6.1f} dBfs  {status}")
    else:
        # Don't print weak signals to reduce clutter
        pass

print("-" * 40)

if strongest_freq:
    print(f"\n🎯 STRONGEST SIGNAL: {strongest_freq} MHz at {strongest_power:.1f} dBfs")
    print(f"\n✅ Set SDR++ to {strongest_freq} MHz")
    print("   Just type this frequency in the SDR++ frequency box!")
    
    # Also try to capture and play it
    print(f"\n📻 Capturing 5 seconds at {strongest_freq} MHz...")
    subprocess.run(f"hackrf_transfer -r /tmp/best_station.iq -f {int(strongest_freq*1e6)} -s 2000000 -n 10000000 -a 1 -l 24 -g 24", 
                   shell=True, stderr=subprocess.DEVNULL)
    
    print("\n💡 In SDR++:")
    print(f"   1. Type: {strongest_freq}")
    print("   2. Mode: WFM")
    print("   3. Click the yellow signal line")
    print("   4. Make sure volume is up!")
else:
    print("\n😕 No strong FM signals found")
    print("   Try:")
    print("   - Check antenna connection")
    print("   - Try different times of day")
    print("   - Scan other bands (AM, Marine VHF, etc.)")