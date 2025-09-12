#!/usr/bin/env python3
"""
Force HackRF frequency change
"""

import subprocess
import time
import sys

def change_frequency(freq_mhz):
    """Change HackRF to specified frequency"""
    freq_hz = int(freq_mhz * 1e6)
    
    print(f"\n{'='*60}")
    print(f"🎯 CHANGING HACKRF FREQUENCY TO {freq_mhz} MHz")
    print(f"{'='*60}\n")
    
    # Kill any existing hackrf processes
    subprocess.run("pkill -9 -f hackrf", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(0.5)
    
    # Reset USB (sometimes helps)
    print("🔄 Resetting HackRF...")
    subprocess.run("hackrf_info", shell=True, capture_output=True)
    time.sleep(0.5)
    
    # Try to capture at new frequency
    print(f"📡 Tuning to {freq_mhz} MHz ({freq_hz} Hz)...")
    cmd = f"timeout 2 hackrf_transfer -r /tmp/freq_test_{freq_mhz}.iq -f {freq_hz} -s 2000000 -n 2000000 -l 32 -g 20"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if "call hackrf_set_freq" in result.stderr:
        print(f"✅ SUCCESS! Frequency changed to {freq_mhz} MHz")
        print(f"📊 Check your PortaPack display - it should show {freq_mhz} MHz")
        return True
    else:
        print(f"❌ Could not change frequency")
        if "Access denied" in result.stderr:
            print("⚠️  HackRF is in use by another application or PortaPack is in control")
            print("\n💡 TO FIX:")
            print("   1. On PortaPack touchscreen, press the button/knob")
            print("   2. Go to 'HackRF Mode' or 'USB' option")
            print("   3. This will allow computer control")
        return False

if __name__ == "__main__":
    # Try multiple frequencies to show we can control it
    frequencies = [
        91.0,   # Calypso Radio
        98.9,   # Kiss FM  
        145.75, # Ham 2m band
        433.92, # ISM band
        121.5,  # Aviation emergency
    ]
    
    print("🔧 DEMONSTRATING FREQUENCY CONTROL")
    print("Watch your PortaPack/HackRF display!\n")
    
    for freq in frequencies:
        if change_frequency(freq):
            print(f"⏰ Staying on {freq} MHz for 3 seconds...")
            time.sleep(3)
        else:
            print("\n⚠️  Cannot control HackRF from computer")
            print("The PortaPack needs to be in USB/HackRF mode")
            sys.exit(1)
    
    print("\n🎉 Frequency control demonstration complete!")
    print("📡 The HackRF successfully changed frequencies")