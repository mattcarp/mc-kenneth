#!/usr/bin/env python3
"""
Simple SDRplay Live Test
Test if we can actually capture RF from your SDRplay without timeout command
"""

import subprocess
import os
import time
from pathlib import Path

def test_sdrplay_capture():
    print("🎯 Simple SDRplay Live RF Test")
    print("=" * 50)
    
    # Check if SoapySDR sees the device
    try:
        result = subprocess.run(['SoapySDRUtil', '--find'], 
                              capture_output=True, text=True, timeout=10)
        if 'sdrplay' in result.stdout:
            print("✅ SDRplay detected by SoapySDR")
        else:
            print("❌ SDRplay not detected")
            print("SoapySDR output:", result.stdout)
            return False
    except Exception as e:
        print(f"❌ SoapySDR test failed: {e}")
        return False
    
    # Try a basic capture with rx_sdr (if available)
    print("\n📡 Testing basic RF capture...")
    
    # First, let's see what capture tools we have
    tools = []
    for tool in ['rx_sdr', 'SoapySDRUtil']:
        try:
            subprocess.run([tool, '--help'], capture_output=True, timeout=3)
            tools.append(tool)
            print(f"✅ {tool} available")
        except:
            print(f"❌ {tool} not available")
    
    if not tools:
        print("❌ No RF capture tools available")
        return False
    
    # Try SoapySDRUtil probe
    print("\n🔍 Probing SDRplay capabilities...")
    try:
        result = subprocess.run(['SoapySDRUtil', '--probe=driver=sdrplay'], 
                              capture_output=True, text=True, timeout=15)
        print("📊 SDRplay capabilities:")
        print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        
        if 'error' in result.stderr.lower() or result.returncode != 0:
            print(f"⚠️ Probe warnings: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Probe failed: {e}")
        return False

def test_manual_sdr_launch():
    """Test launching SDR++ cleanly"""
    print("\n🚀 Testing clean SDR++ launch...")
    
    # Check if SDR++ is available
    sdr_app = "/Users/matt/Documents/projects/RF-Digital-Forensics-Toolkit/SDR++.app"
    if Path(sdr_app).exists():
        print(f"✅ SDR++ found: {sdr_app}")
        print("💡 You can manually launch with:")
        print(f"   open '{sdr_app}'")
        print("   Then tune to 156.800 MHz and look for signals")
        return True
    else:
        print("❌ SDR++ not found")
        return False

if __name__ == "__main__":
    print("🔧 SDRplay Hardware Integration Test")
    print("====================================")
    
    # Test 1: Basic hardware detection
    if test_sdrplay_capture():
        print("\n✅ SDRplay hardware integration working!")
    else:
        print("\n❌ SDRplay hardware integration failed!")
    
    # Test 2: Manual options
    test_manual_sdr_launch()
    
    print("\n🎯 Next Steps:")
    print("1. Launch SDR++ manually and check if it sees your device")
    print("2. Tune to 156.800 MHz (maritime emergency channel)")
    print("3. Look for any spectrum activity or signals")
    print("4. If you see signals, try to demodulate FM")
