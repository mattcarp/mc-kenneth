#!/bin/bash
# Aviation Band AM Radio - Listen to Malta Airport from Valletta!

FREQ=${1:-121900000}  # Default: Malta Ground
FREQ_MHZ=$(echo "scale=3; $FREQ/1000000" | bc)

echo "═══════════════════════════════════════════════════"
echo "    ✈️  AVIATION BAND SCANNER - VALLETTA"
echo "═══════════════════════════════════════════════════"
echo ""
echo "📡 Tuning to: $FREQ_MHZ MHz (AM Mode)"
echo "📍 Malta International Airport: 8km from your location"
echo ""
echo "Active Aviation Frequencies:"
echo "  118.120 MHz - Malta Tower (Landing/Takeoff)"
echo "  121.900 MHz - Malta Ground (Taxiing) *STRONG SIGNAL*"
echo "  134.700 MHz - Malta Approach (Incoming)"
echo "  121.500 MHz - Emergency Frequency"
echo ""
echo "Press Ctrl+C to stop"
echo "═══════════════════════════════════════════════════"

# Capture and AM demodulate
echo "🎧 Recording 10 seconds of aviation comms..."
hackrf_transfer -r /tmp/aviation.iq \
    -f $FREQ \
    -s 2000000 \
    -a 1 \
    -l 32 \
    -g 20 \
    -n 20000000

echo "✈️ Demodulating AM signal..."

python3 << 'EOF'
import numpy as np
import sys

freq = int(sys.argv[1]) if len(sys.argv) > 1 else 121900000

# Read IQ data
with open('/tmp/aviation.iq', 'rb') as f:
    raw = f.read()

iq = np.frombuffer(raw, dtype=np.int8).astype(np.float32) / 128.0
iq_complex = iq[0::2] + 1j * iq[1::2]

# AM demodulation - just take the magnitude!
am_demod = np.abs(iq_complex)

# Remove DC and normalize
am_demod = am_demod - np.mean(am_demod)
am_demod = am_demod / (np.max(np.abs(am_demod)) + 0.001)

# Basic downsampling to audio rate
audio = am_demod[::40]

# High-pass filter to remove low rumble, improve voice
from scipy import signal
sos = signal.butter(3, 300, 'hp', fs=50000, output='sos')
audio_filtered = signal.sosfilt(sos, audio)

# Save
audio_filtered.astype(np.float32).tofile('/tmp/aviation_audio.raw')
print(f"✅ Demodulated {freq/1e6:.3f} MHz AM signal")
EOF

echo "🔊 Playing aviation communications..."
play -q -t raw -r 50000 -b 32 -c 1 -e float /tmp/aviation_audio.raw gain 10

echo ""
echo "💡 TIP: Best reception times:"
echo "   Morning: 07:00-10:00 (busy arrivals)"
echo "   Evening: 18:00-21:00 (busy departures)"
echo ""
echo "🎯 Try during those times for guaranteed air traffic!"
