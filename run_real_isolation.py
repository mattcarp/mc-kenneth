#!/usr/bin/env python3
"""Run real ElevenLabs voice isolation on RF capture"""

from dotenv import load_dotenv
load_dotenv()
import os
from pathlib import Path
from elevenlabs_voice_isolator import VoiceIsolator

# Create isolator instance
isolator = VoiceIsolator()
print(f'✅ Voice Isolator initialized')
print(f'API Key configured: {"Yes" if isolator.api_key else "No"}')

# Process the FM radio capture
test_file = Path('REAL_RTL_CAPTURE_FM_Radio_Test_88.5MHz_20250912_194650.wav')
if test_file.exists():
    print(f'\n🎯 Processing real RF capture: {test_file.name}')
    result = isolator.isolate_voice(test_file)
    if result:
        print(f'\n✨ SUCCESS! Voice isolation complete')
        print(f'Original: {result["original_file"]}')
        print(f'Isolated: {result["isolated_file"]}')
        print(f'Duration: {result["duration"]:.1f}s')
        print(f'Cost: ${result["cost"]:.3f}')
    else:
        print('❌ Processing failed')
else:
    print(f'❌ File not found: {test_file}')
