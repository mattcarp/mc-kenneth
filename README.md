# RF Digital Forensics Toolkit - Kenneth

## OpenWebRX+ Integration
This project uses **OpenWebRX+** (https://github.com/luarvique/openwebrx) as the base platform for web-based SDR operations. OpenWebRX+ is chosen for its:
- Open source nature allowing full customization
- Active development and maintenance
- Professional SDRplay RSPdx/RSPduo support
- API access for our AI integrations
- Modern Python codebase
## Advanced Signal Analysis & Security Research Suite

**Hardware:**
- SDRplay RSPdx or RSPduo (1kHz - 2GHz, 14-bit ADC, superior dynamic range)
- tinySA Ultra+ Spectrum Analyzer (100kHz - 7.3GHz)
- Scout KS-23A Marine Antenna (wideband coverage)

**Location:** Victoria, Gozo, Malta (perfect Mediterranean surveillance position)

## PROJECT MISSION: DUAL PURPOSE HUMANITARIAN & SECURITY

### 🚨 MISSION 1: CATCH BAD GUYS
Detect malicious intent, threats, and criminal activity across all RF frequencies

### 🆘 MISSION 2: SAVE LIVES  
Identify people in distress, emergency calls, and those needing immediate help

**Coverage:** All frequencies (1 MHz - 6 GHz) | All languages | 24/7 monitoring
**Response:** Real-time SMS alerts → Coordinated emergency response

### Phase 1: Signal Fingerprinting Engine
```cpp
class RFFingerprinting {
    struct DeviceSignature {
        double frequency_accuracy;
        double phase_noise_profile;
        vector<double> harmonic_distortion;
        string crystal_signature;
        double power_ramping_characteristics;
    };
    
    DeviceSignature analyzeTransmitter(Signal signal);
    bool matchKnownDevice(DeviceSignature sig);
    void buildFingerprintDatabase();
};
```

### Phase 2: Protocol Vulnerability Scanner
- **Weak encryption detection** (predictable keys, poor randomness)
- **Implementation flaw identification** (timing attacks, side channels)
- **Protocol reconstruction** from unknown digital signals
- **Traffic pattern analysis** for behavioral fingerprinting

### Phase 3: Rogue Transmitter Hunter
- **Triangulation using both devices**
- **Interference source geolocation**
- **Illegal frequency usage detection**
- **Jamming attempt identification**

### Phase 4: Security Assessment Framework
- **RF emissions analysis** (TEMPEST-style)
- **Side-channel attack detection**
- **Unintentional information leakage**
- **Device vulnerability assessment**

## Development Architecture

### Core Components:
1. **Signal Acquisition Engine** (SDRplay interface via SoapySDR)
2. **Spectrum Analysis Engine** (tinySA integration)
3. **Digital Forensics Algorithms** (custom DSP)
4. **Threat Detection System** (AI/ML classification)
5. **Evidence Collection Framework** (legal-grade documentation)
6. **Geolocation Subsystem** (triangulation algorithms)

### Target Applications:
- **Maritime security** (detecting smuggler communications)
- **Aviation security** (rogue transmitter detection)
- **Cybersecurity research** (RF side-channel analysis)
- **Regulatory compliance** (illegal transmitter hunting)
- **Research & education** (RF security demonstrations)

## Mediterranean Use Cases:
- **Detect illegal fishing boat communications**
- **Find smuggling operation frequencies**
- **Identify rogue maritime transmitters**
- **Analyze suspicious aircraft communications**
- **Security assessment of critical infrastructure**

## Next Session Goals:
1. **Design the core architecture**
2. **Build signal fingerprinting algorithms**
3. **Create device identification database**
4. **Implement basic vulnerability scanning**
5. **Test with real Mediterranean signals**

**Location advantage:** Malta's position makes it perfect for intercepting traffic between Europe, North Africa, and the Middle East!


## 🔊 Audio Processing & Noise Suppression (NEW!)

### ElevenLabs Integration
Advanced noise suppression for RF-captured audio using state-of-the-art AI:

```python
from elevenlabs_integration import ElevenLabsNoiseProcessor, AudioQuality

# Initialize processor
processor = ElevenLabsNoiseProcessor()

# Process noisy RF capture with extreme noise suppression
result = processor.process_audio(
    "captures/marine_vhf_noisy.wav",
    quality=AudioQuality.HIGH
)

# Get cleaned audio path
print(f"Cleaned audio: {result.processed_path}")
```

### Setup
```bash
# Install dependencies and configure
./setup_elevenlabs.sh

# Set your API key
export ELEVENLABS_API_KEY='your_key_here'

# Test the integration
python3 test_elevenlabs.py
```

### Features
- **Extreme noise suppression** - Handles severe RF noise, static, interference
- **RF-specific preprocessing** - Removes carrier artifacts, intermodulation 
- **Multi-quality modes** - Draft/Standard/High based on signal importance
- **Smart caching** - Reduces API costs by caching processed audio
- **Fallback processing** - Local noise reduction when API unavailable
- **Batch processing** - Process multiple captures in parallel

### Pipeline Architecture
```
RF Capture → Demodulation → RF Preprocessing → ElevenLabs API → Speech-to-Text
     ↓            ↓               ↓                  ↓              ↓
  SDRplay     AM/FM/SSB    Remove artifacts   AI noise removal   Whisper/STT
```

### Use Cases
- **Maritime VHF** - Clean up ship-to-ship communications
- **Aviation** - Enhance ATC communications with engine noise
- **Emergency** - Extract clear audio from weak/noisy signals
- **SIGINT** - Process intercepted communications for analysis

---

## Next Session Goals:
1. **Integrate OpenAI Whisper** for transcription
2. **Add OpenAI Realtime API** for speech-to-speech
3. **Build real-time processing pipeline**
4. **Create Mediterranean maritime intelligence dashboard**
5. **Train custom models** on RF-specific noise patterns

**Location advantage:** Malta's position makes it perfect for intercepting traffic between Europe, North Africa, and the Middle East!