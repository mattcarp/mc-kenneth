#!/usr/bin/env python3
"""Debug what's in the isolated file"""

import subprocess
import json

# Get detailed info about both files
print("🔍 Analyzing audio files...\n")

original = "/Users/matt/Documents/projects/RF-Digital-Forensics-Toolkit/REAL_RTL_CAPTURE_FM_Radio_Test_88.5MHz_20250912_194650.wav"
isolated = "/Users/matt/Documents/projects/RF-Digital-Forensics-Toolkit/elevenlabs_isolated/isolated_REAL_RTL_CAPTURE_FM_Radio_Test_88.5MHz_20250912_194650.wav"

print("ORIGINAL FILE:")
print("-" * 40)
subprocess.run(["file", original])
print()

print("ISOLATED FILE:")
print("-" * 40)
subprocess.run(["file", isolated])
print()

# Try to get any text/metadata from the MP3
print("Checking for ID3 tags or metadata in isolated file:")
print("-" * 40)
subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", isolated])
