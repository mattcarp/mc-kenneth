# RF Digital Forensics Toolkit - Complete Documentation

## 🚀 Quick Start

```bash
# Ensure Node LTS is active
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use lts/*

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install

# Run tests
npm test
```

## 📚 Project Structure

```
RF-Digital-Forensics-Toolkit/
├── 📋 Documentation
│   ├── README.md                 # This file
│   ├── tests/README.md          # Test suite documentation
│   ├── MISSION.md               # Kenneth maritime intelligence mission
│   ├── KENNETH_PRD.md          # Product requirements document
│   └── ARCHITECTURE.md         # System architecture
│
├── 🧪 Testing Infrastructure
│   ├── playwright.config.ts    # Playwright configuration
│   ├── run-tests.sh           # Test runner script
│   ├── tests/                 # Comprehensive test suite
│   │   ├── core/             # Core WebSDR tests
│   │   ├── waterfall/        # WebGL visualization tests
│   │   ├── rf-capture/       # Signal processing tests
│   │   ├── integration/      # OpenWebRX+ integration
│   │   ├── performance/      # Performance benchmarks
│   │   ├── e2e/             # End-to-end workflows
│   │   └── utils/           # Test utilities
│   └── kenneth-websdr/       # Kenneth WebSDR application
│       └── testsprite_tests/ # AI-generated business tests
│
├── 🛠️ SDR Software
│   ├── SDR++.app/            # SDR++ application
│   ├── sdrpp_macos_arm.zip  # SDR++ installer
│   └── setup_sdrpp_rspdx.sh # SDRplay setup script
│
└── 🔧 Configuration & Scripts
    ├── setup-node-lts.sh     # Node.js LTS installer
    ├── config/               # Application configs
    └── package.json         # Project dependencies
```

## 🧪 Test Suite Documentation

### Running Tests

```bash
# All tests
npm test

# Specific test suites
npm run test:core        # Core functionality
npm run test:waterfall   # Waterfall display
npm run test:rf          # RF capture
npm run test:integration # OpenWebRX+ integration
npm run test:performance # Performance benchmarks
npm run test:e2e         # End-to-end workflows

# Interactive UI
npm run test:ui

# View test report
npm run test:report
```

### Test Categories

| Category | Purpose | Key Tests |
|----------|---------|-----------|
| **Core** | Basic WebSDR functionality | Interface loading, frequency control, audio |
| **Waterfall** | WebGL spectrum display | Rendering, real-time updates, click-to-tune |
| **RF Capture** | Signal processing | SDR connection, demodulation, signal strength |
| **Integration** | OpenWebRX+ features | WebSocket, bookmarks, digital modes |
| **Performance** | Speed & resources | Load time <3s, 30+ FPS, <500ms latency |
| **E2E** | Complete workflows | Maritime monitoring, emergency detection |

### Maritime Frequency Reference

| Channel | Frequency (MHz) | Purpose |
|---------|----------------|---------|
| 16 | 156.8 | International Distress |
| 70 | 156.525 | DSC Digital Calling |
| 6 | 156.3 | Ship-to-Ship |
| 13 | 156.65 | Navigation Safety |
| 87 | 161.975 | AIS 1 |
| 88 | 162.025 | AIS 2 |

## 🔧 Development Setup

### Prerequisites

1. **Node.js LTS v22.19.0**
   ```bash
   # Check version
   node --version  # Should show v22.19.0
   
   # If not, activate NVM and use LTS
   export NVM_DIR="$HOME/.nvm"
   [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
   nvm use lts/*
   ```

2. **SDRplay API** (for RSPdx-R2)
   - Download from: https://www.sdrplay.com/downloads/
   - Install the .pkg file
   - Restart SDR++ after installation

3. **SDR++ Application**
   - Already installed in `SDR++.app/`
   - Launch: `./SDR++.app/Contents/MacOS/sdrpp`

### Environment Setup

```bash
# 1. Ensure Node LTS
./setup-node-lts.sh

# 2. Install dependencies
npm install

# 3. Install Playwright browsers
npx playwright install

# 4. Verify setup
npm run test:core
```

## 📡 RF Hardware

### Supported Devices
- **RSPdx-R2** - Primary SDR (10 kHz - 2 GHz)
- **HackRF One** - Secondary SDR with PortaPack
- **RTL-SDR** - Budget option for testing

### Key Frequencies
- Marine VHF: 156-162 MHz
- Aviation Emergency: 121.5 MHz
- Military Emergency: 243.0 MHz
- ISS: 145.8 MHz
- NOAA Weather: 162.4-162.55 MHz

## 🚢 Kenneth Maritime Intelligence

### Mission
Real-time maritime RF monitoring with AI-powered emotional analysis for detecting distress situations in Malta waters.

### Core Features
1. **Multi-frequency Monitoring** - Simultaneous monitoring of marine channels
2. **Emotion Detection** - AI analysis of voice stress patterns
3. **Waterfall Display** - Real-time WebGL spectrum visualization
4. **Alert System** - Automated distress detection and alerts
5. **Recording** - Automatic capture of emergency transmissions

### Technical Stack
- **Frontend**: TypeScript, WebGL, WebSockets
- **Backend**: Python, OpenWebRX+, SDR drivers
- **Testing**: Playwright, TestSprite
- **AI**: ElevenLabs for voice analysis

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: '22'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Install Playwright
        run: npx playwright install --with-deps
        
      - name: Run tests
        run: npm test
        
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/
```

## 📝 Git Workflow

```bash
# Feature development
git checkout -b feature/maritime-alerts
npm run test:e2e  # Test your changes
git add .
git commit -m "feat: add maritime alert system"
git push origin feature/maritime-alerts

# Create PR with test results
```

## 🐛 Troubleshooting

### Common Issues

**Node Version Issues**
```bash
# Always ensure NVM is loaded and using LTS
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use lts/*
node --version  # Should be v22.19.0
```

**SDR Not Detected**
```bash
# Check SDRplay API
ls /usr/local/lib/libsdrplay*

# Check USB permissions
ls -la /dev/bus/usb/
```

**Playwright Issues**
```bash
# Reinstall browsers
npx playwright install --force

# Run with debug
npm run test:debug
```

**OpenWebRX Not Starting**
```bash
# Check port availability
lsof -i:8073

# Start mock server
python3 -m http.server 8073
```

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev)
- [SDRplay API Guide](https://www.sdrplay.com/docs/)
- [OpenWebRX+ Wiki](https://github.com/luarvique/openwebrx/wiki)
- [Marine VHF Channels](https://www.navcen.uscg.gov/?pageName=vhfMarine)

## 👥 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

ISC License - See LICENSE file for details

---

**Last Updated**: September 4, 2025  
**Node Version**: v22.19.0 LTS  
**Test Coverage**: Comprehensive  
**Architecture**: Tufte-Inspired (Maximum information, minimum clutter)
