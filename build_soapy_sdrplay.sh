#!/bin/bash
# Build SoapySDRPlay3 from source for macOS
# This enables SDRplay support in SoapySDR-compatible software

echo "🔧 Building SoapySDRPlay3 for SDRplay support"
echo "=============================================="

# Check prerequisites
if ! command -v cmake &> /dev/null; then
    echo "Installing cmake..."
    brew install cmake
fi

if ! command -v SoapySDRUtil &> /dev/null; then
    echo "❌ SoapySDR not found. Install with: brew install soapysdr"
    exit 1
fi

# Create build directory
BUILD_DIR="$HOME/soapy-sdrplay-build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Clone the repository
echo "📥 Cloning SoapySDRPlay3..."
git clone https://github.com/pothosware/SoapySDRPlay3.git
cd SoapySDRPlay3

# Build and install
echo "🔨 Building..."
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local
make -j4

echo ""
echo "📦 To install (requires sudo):"
echo "   cd $BUILD_DIR/SoapySDRPlay3/build"
echo "   sudo make install"
echo ""
echo "Then test with: SoapySDRUtil --find"
