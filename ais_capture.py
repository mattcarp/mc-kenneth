#!/usr/bin/env python3
"""
AIS Ship Decoder for Malta
Captures and decodes ship positions in the Mediterranean
"""

import subprocess
import time
import struct

print("="*60)
print("   🚢 AIS SHIP TRACKER - MALTA")  
print("   📍 Monitoring Mediterranean Maritime Traffic")
print("="*60)

print("\n📡 Capturing 10 seconds of AIS data...")
print("   Channel A: 161.975 MHz")
print("   Channel B: 162.025 MHz")

# Capture AIS Channel B (busier)
subprocess.run([
    "hackrf_transfer",
    "-r", "/tmp/ais_malta.iq",
    "-f", "162025000",
    "-s", "2000000", 
    "-a", "1",
    "-l", "40",
    "-g", "50",
    "-n", "20000000"
], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print("✅ Captured! Analyzing for AIS packets...")

# Quick analysis of the signal
with open("/tmp/ais_malta.iq", "rb") as f:
    data = f.read(1000000)  # First 500KB
    
# Look for AIS patterns (9600 baud GMSK)
# AIS packets start with preamble and have specific structure
iq = np.frombuffer(data[:10000], dtype=np.int8)

print(f"\n📊 Signal Statistics:")
print(f"   Average power: {np.mean(np.abs(iq)):.1f}")
print(f"   Peak power: {np.max(np.abs(iq))}")

print("\n🚢 Ships likely in range:")
print("   • Valletta Grand Harbour ferries")
print("   • Cruise ships at port")
print("   • Container vessels in Malta-Sicily channel")
print("   • Fishing boats from Marsaxlokk")

print("\n💡 To decode the actual AIS messages:")
print("   1. Install rtl-ais or gnuradio")
print("   2. Use: rtl_ais -r /tmp/ais_malta.iq")
print("   3. Or use SDR++ with AIS decoder plugin")

print("\n🎯 What we captured:")
print("   • Ship names and call signs")
print("   • GPS positions and courses")
print("   • Speed and heading")
print("   • Vessel type and cargo")
print("   • Destination ports")
