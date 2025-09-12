# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
RF Digital Forensics Toolkit - A defensive security platform for radio frequency signal analysis, threat detection, and digital forensics. This toolkit is designed for security research, regulatory compliance, and defensive security operations using SDRplay hardware and tinySA Ultra+ spectrum analyzer.

## 🚨 CRITICAL UI/UX REQUIREMENTS - NEVER CHANGE THESE

### Demo Page Identity (kenneth_demo.html, sigint_demo_updated.html, mc_sigint_demo.html)
**THE FOLLOWING MUST NEVER BE CHANGED:**
1. **H1 Title:** Must ALWAYS be "Kenneth" - this is the project identity
2. **Subtitle:** Must ALWAYS be "Goals: 1. Detect bad actors, 2. Help those in distress"

These two elements are the core identity of the project and define our mission. Any demo or UI must preserve these exactly as written. No variations, no rewording, no "improvements."

### UI/UX Principles
- Focus on engineering data, not marketing copy
- Show real technical specifications (sample rates, gain settings, frequencies)
- Display actual results from SDRplay captures and processing
- No sales pitch language or "discovery" boxes
- Keep operational security - don't reveal specific tools/methods unnecessarily

## 🎨 FRONTEND ARCHITECTURE REQUIREMENTS

### Technology Stack (Kenneth WebSDR)
The Kenneth WebSDR frontend (`/kenneth-websdr`) MUST use:

**Core Framework:**
- **Next.js 15+** with App Router (latest stable version)
- **TypeScript** for type safety
- **Port 4000** for development and production (NOT 3000)

**UI Component Libraries (in order of preference):**
1. **shadcn/ui** - Primary component library (built on Radix UI)
2. **Radix UI primitives** - When you need lower-level control
3. **Vercel AI Elements** - For AI-powered UI features (https://github.com/vercel/ai-elements)
   - Use components like StreamingText, GenerativeUI, etc.
   - NOT the Vercel AI SDK - only the UI elements/components
   - Only when appropriate for RF signal analysis displays
4. Custom components - Only when absolutely necessary

**Styling & Animation:**
- **Tailwind CSS** - All styling should use Tailwind utilities
- **class-variance-authority (CVA)** - For component variants
- **tailwind-merge** - For merging Tailwind classes
- **Framer Motion** - For animations and transitions

**Data Visualization:**
- **Recharts** or **Tremor** - For charts and graphs
- **WebGL/Three.js** - Only for the waterfall spectrum display
- **D3.js** - For complex custom visualizations

**State Management:**
- **Zustand** or **Jotai** - For global state
- **React Query/TanStack Query** - For server state
- **React Hook Form** - For forms

**Key Packages to Install:**
```bash
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tabs
npm install class-variance-authority tailwind-merge clsx
npm install framer-motion
npm install recharts
npm install @vercel/ai-elements  # When needed for AI features
```

## 🎨 MAC Design System Integration

**CENTRALIZED DESIGN SYSTEM**: All MAC design files are centralized in `~/Documents/projects/mc-design-system/`

### Design System References
The following files are symlinked from the central mc-design-system repository:
- **CSS Reference**: `src/styles/mac-design-system.css` → `~/Documents/projects/mc-design-system/tokens/mac-design-system.css`
- **Design Principles**: `context/mac-design-principles.md` → `~/Documents/projects/mc-design-system/docs/mac-design-principles.md`
- **Design Review Tool**: `design-review-automation.js` → `~/Documents/projects/mc-design-system/tools/design-review-automation.js`
- **Fiona Agent**: `~/Documents/projects/mc-design-system/agents/fiona-design-review.md`

### Design Review Commands
```bash
# Run comprehensive design review for RF interfaces
node ~/Documents/projects/mc-design-system/tools/design-review-automation.js

# Use slash command for full 8-phase review
/design-review
```

### When Making UI Changes for RF Applications
1. **Reference MAC tokens**: Always use `--mac-*` CSS variables for RF interface consistency
2. **Follow typography weights**: Only use 100, 200, 300, 400 for professional RF tool appearance  
3. **Maintain spacing grid**: 8px base unit for technical interface precision
4. **Use MAC components**: Prefer `.mac-*` classes for RF dashboard elements
5. **Validate with Fiona**: Run design review before committing RF UI changes

### RF-Specific Design Considerations
- **Technical Readouts**: Ensure high contrast for frequency displays and signal data
- **Dark Mode Optimized**: Professional dark interface for extended RF monitoring
- **Data Visualization**: MAC tokens work with Recharts/D3.js for spectrum displays
- **Alert States**: Use MAC state colors for signal detection and threat indicators

### Design System Development
- **Central repo**: `~/Documents/projects/mc-design-system/`
- **Edit once, update everywhere**: Changes automatically reflect in SIAM, RF toolkit, and other projects
- **Development-only**: These are guides and validators, not production dependencies

## 🎉 BREAKTHROUGH: Audio Isolation Integration SUCCESS!

**THE GAME-CHANGER:** We've successfully integrated ElevenLabs Audio Isolation API for EXTREME noise reduction on RF captures! This turns static-filled radio captures into CRYSTAL CLEAR SPEECH!

### Quick Setup
```bash
export ELEVENLABS_API_KEY='your_key_here'  # Get from elevenlabs.io
python3 process_malta_fm.py                # Process RF captures
```

### Results
- **Before:** Static-filled, noisy RF captures from SDR
- **After:** Crystal clear speech, professional audio quality
- **Works on:** Marine VHF, Aviation, FM radio, any RF audio
- **Requirements:** Audio must be >4.6 seconds, returns MP3 (320kbps)

### Processing Pipeline (BREAKTHROUGH DISCOVERY!)
1. **SDRplay captures** raw IQ data
2. **Demodulation** (FM/AM/SSB)
3. ~~**Local preprocessing**~~ **SKIP THIS! NOT NEEDED!**
4. **ElevenLabs API** = MAGIC noise removal!

**DISCOVERY:** We can handle raw RF audio directly
No preprocessing needed! Tested and confirmed - the AI removes:
- 50Hz power line hum (Malta)
- RF interference and static
- Background noise
- ALL THE SHIT automatically!

Just throw raw demodulated audio at ElevenLabs and it comes out CRYSTAL CLEAR!

## Key Commands

### Testing & Development
```bash
# Test hardware connections
python tests/test_hardware.py

# Start API server (runs on port 8000, includes Swagger UI)
./start_api.sh
# Or directly:
python3 -m uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

# Frontend Development (ALWAYS use port 4000, not 3000)
cd kenneth-websdr
npm run dev  # Runs on port 4000
npm run build && npm start  # Production, also port 4000

# Run tests
pytest tests/

# Format code
black src/ tests/
ruff check src/ tests/

# Type checking
mypy src/
```

### RF Operations
```bash
# FM radio operations
./fm_listen.sh          # Listen to FM radio
./fm_station_finder.sh  # Find active FM stations
./aviation_scanner.sh   # Scan aviation frequencies

# Signal hunting
python signal_hunter.py
python find_best_signal.py
```

## Architecture

### Core Components
- **src/rf_forensics_core.py** - Main forensics engine with signal fingerprinting and analysis
- **src/sdrplay_interface.py** - SDRplay hardware interface for signal capture
- **src/tinysa_interface.py** - TinySA Ultra+ spectrum analyzer interface
- **api_server.py** - FastAPI server providing REST endpoints for all RF operations

### MCP Server Agents
- **mcp_server/taskmaster_ai_mcp.py** - Task orchestration and management
- **mcp_server/rf_analyst_agent.py** - Signal analysis agent
- **mcp_server/threat_hunter_agent.py** - Threat detection agent
- **mcp_server/taskmaster_full_spectrum.py** - Full spectrum monitoring

### Hardware Requirements
- SDRplay RSPdx or RSPduo (1kHz - 2GHz, 14-bit ADC)
- tinySA Ultra+ Spectrum Analyzer (100kHz - 7.3GHz)
- Operates from Malta location (Mediterranean surveillance position)

## API Documentation
When server is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI spec: http://localhost:8000/openapi.json

## Security Context
This is a defensive security toolkit for:
- Signal fingerprinting and device identification
- Detecting rogue transmitters and illegal frequency usage
- RF emissions analysis (TEMPEST-style)
- Maritime and aviation security monitoring
- Regulatory compliance and threat hunting

## Development Notes
- Always check SDRplay connection before operations: `SoapySDRUtil --find`
- API server includes demo mode when hardware is not connected
- FM demodulation tools have multiple implementations (fm_demod_proper.py, fm_demod_working.py) - use the working version
- Location-specific: Optimized for Mediterranean signal environment (Malta)

## SDRplay Connection and Control

### Checking SDRplay Connection
```bash
# Check if SDRplay is detected
SoapySDRUtil --find

# Get detailed device info
SoapySDRUtil --probe="driver=sdrplay"
```

### Common SDRplay Issues and Fixes

**If SDRplay is not detected:**
1. Check USB connection and try different ports
2. Ensure SDRplay API service is running:
   ```bash
   # macOS - restart the service
   sudo killall sdrplay_apiService
   # The service should auto-restart
   ```
3. Check for conflicting processes
4. Verify SDRplay API is installed (version 3.x required)

## Hardware Connection Guide

### SDRplay RSPdx/RSPduo Setup

#### Prerequisites
1. Install SDRplay API (version 3.x):
   ```bash
   # Download from www.sdrplay.com/downloads/
   # Run the installer package for macOS
   ```

2. Install SoapySDR and SoapySDRPlay:
   ```bash
   brew install soapysdr
   brew install soapysdrplay3
   ```

#### Connection Verification
```bash
# Check if SDRplay is detected
SoapySDRUtil --find

# Should show something like:
# Found device 0
#   driver = sdrplay
#   label = SDRplay Dev0 RSPdx 1234567890

# Get detailed info
SoapySDRUtil --probe="driver=sdrplay"
```

#### Python Integration
```python
import SoapySDR

# List available devices
devices = SoapySDR.Device.enumerate()
for d in devices:
    print(d)

# Connect to SDRplay
sdr = SoapySDR.Device({"driver": "sdrplay"})
```

### SDRplay Advantages over HackRF
- **14-bit ADC** vs 8-bit: Superior dynamic range
- **Better sensitivity**: Lower noise floor
- **Multiple antenna inputs**: Diversity reception
- **Built-in LNA and filters**: Better signal quality
- **1kHz to 2GHz continuous**: Wider frequency range
- this mission for this project is twofold: catch bad actors, and help those in distress. we'll use all of our AI and SigInt tools in pursruit of those goals.
- stop mentioning ElevenLabs in the UI. refer to it as Kenneth.

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
