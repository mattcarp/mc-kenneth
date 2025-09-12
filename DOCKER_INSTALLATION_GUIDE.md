# 🐳 OPENWEBRX+ DOCKER INSTALLATION GUIDE
## The BEST Way to Run OpenWebRX+ on macOS

---

## ✅ WHY DOCKER IS BETTER

### Native Installation Problems on macOS:
- ❌ CSDR doesn't compile easily on Mac
- ❌ Liquid-DSP has ARM64 issues  
- ❌ Python library conflicts
- ❌ USB permissions complexity
- ❌ Hours of debugging

### Docker Solution:
- ✅ **One command to run everything**
- ✅ All dependencies included
- ✅ Guaranteed to work
- ✅ Easy updates
- ✅ Professional deployment method

---

## 📋 STEP-BY-STEP INSTALLATION

### Step 1: Install Docker Desktop for Mac
1. Download from: https://www.docker.com/products/docker-desktop/
2. Choose **Apple Silicon** version (for M1/M2/M3 Macs)
3. Open the .dmg file
4. Drag Docker to Applications
5. Open Docker Desktop from Applications
6. Wait for "Docker Desktop is running" (green icon)

### Step 2: Run Our Script
```bash
cd /Users/mattcarp/Documents/projects/rf-forensics-toolkit
./install_openwebrx_docker.sh
```

### Step 3: Access OpenWebRX+
Open browser to: http://localhost:8073

---

## 🎯 ADVANTAGES OF DOCKER APPROACH

### 1. **Everything Pre-Installed**
- CSDR ✅
- Liquid-DSP ✅
- SoapySDR ✅
- All decoders ✅
- All dependencies ✅

### 2. **HackRF Support Built-In**
```yaml
devices:
  - /dev/bus/usb  # Passes through USB devices
privileged: true  # Allows hardware access
```

### 3. **Easy Configuration**
- Edit: `~/kenneth-openwebrx-config/config_webrx.py`
- Restart: `docker restart kenneth-websdr`
- No recompilation needed!

### 4. **Professional Deployment**
- This is how production systems run
- Easy backup: just save config directory
- Easy migration: copy container to new machine
- Auto-restart on crashes

---

## 🚀 QUICK START COMMANDS

### After Docker Desktop is installed:
```bash
# Pull OpenWebRX+ image
docker pull jketterl/openwebrx:latest

# Run with HackRF support
docker run -d \
  --name kenneth-websdr \
  -p 8073:8073 \
  --privileged \
  --device /dev/bus/usb \
  jketterl/openwebrx:latest

# Check it's running
docker ps

# View logs
docker logs -f kenneth-websdr

# Open browser
open http://localhost:8073
```

---

## 📡 HACKRF CONNECTION IN DOCKER

### The container needs USB access:
```bash
# List USB devices
ls /dev/bus/usb/*/*

# Run with USB access
docker run --device /dev/bus/usb --privileged ...
```

### If HackRF not detected:
1. Unplug and replug HackRF
2. Restart Docker container
3. Check Docker Desktop has USB permission

---

## 🔧 TROUBLESHOOTING

### Port 8073 already in use:
```bash
# Find what's using it
lsof -i :8073

# Kill it or use different port
docker run -p 8074:8073 ...
```

### Container won't start:
```bash
# Check logs
docker logs kenneth-websdr

# Remove and recreate
docker rm kenneth-websdr
docker run ...
```

### HackRF not found:
```bash
# Check USB in container
docker exec kenneth-websdr ls /dev/bus/usb

# Restart with more permissions
docker run --privileged -v /dev/bus/usb:/dev/bus/usb ...
```

---

## 📊 DOCKER VS NATIVE COMPARISON

| Feature | Native Install | Docker |
|---------|---------------|--------|
| Setup Time | 2-4 hours | 5 minutes |
| Dependencies | Manual install | Included |
| Updates | Recompile | `docker pull` |
| Conflicts | Likely | Isolated |
| Production Ready | No | Yes |
| Reproducible | No | Yes |

---

## 🎯 BOTTOM LINE

**DOCKER IS THE WAY TO GO!**

1. Install Docker Desktop (5 min)
2. Run our script (1 min)
3. OpenWebRX+ running (instant)
4. Start catching bad guys! 🚨

No compilation, no dependencies, no conflicts. Just pure RF intelligence power!

---

*From Malta, we protect the Mediterranean - now with Docker efficiency!* 🇲🇹