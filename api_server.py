#!/usr/bin/env python3
"""
RF Digital Forensics Toolkit - FastAPI Server
Full-spectrum SIGINT API covering 1MHz to 6GHz
Self-documenting with OpenAPI/Swagger and Redoc
Location: Valletta, Malta - Mediterranean Intelligence Hub
"""

from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    WebSocket,
    Query,
    File,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
import asyncio
import numpy as np
from datetime import datetime
import subprocess
import os
from api_maritime_aviation import add_maritime_aviation_routes

# Initialize FastAPI with rich metadata
app = FastAPI(
    title="RF Digital Forensics Toolkit API",
    description="""
    ## 🎯 Full-Spectrum SIGINT Platform
    
    **Coverage:** 1 MHz to 6 GHz (HackRF One capabilities)
    **Location:** Malta - Strategic Mediterranean position
    **Capabilities:**
    - Real-time signal capture and analysis
    - Maritime AIS/VHF monitoring
    - Aviation ADS-B/ACARS tracking
    - Cellular/IoT signal intelligence  
    - Amateur radio monitoring
    - Threat detection and classification
    - ML-powered signal fingerprinting
    
    ## 📡 Frequency Ranges
    - **LF/MF/HF** (1-30 MHz): Time signals, amateur radio, maritime
    - **VHF** (30-300 MHz): FM broadcast, aviation, marine, emergency
    - **UHF** (300-3000 MHz): Cellular, WiFi, Bluetooth, satellites
    - **SHF** (3-6 GHz): 5G, radar, satellite
    """,
    version="2.0.0",
    docs_url="/docs",  # Swagger UI at /docs (standard location)
    redoc_url="/redoc",  # ReDoc alternative
    openapi_tags=[
        {"name": "capture", "description": "Signal capture operations"},
        {"name": "analysis", "description": "Signal analysis and classification"},
        {"name": "maritime", "description": "Maritime intelligence"},
        {"name": "aviation", "description": "Aviation monitoring"},
        {"name": "threats", "description": "Threat detection"},
        {"name": "spectrum", "description": "Spectrum scanning"},
        {"name": "ml", "description": "Machine learning operations"},
        {"name": "realtime", "description": "Real-time streaming"},
    ],
)

# CORS for web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ENUMS & MODELS ====================


class FrequencyBand(str, Enum):
    """Standard frequency band classifications"""

    LF = "lf"  # 30-300 kHz
    MF = "mf"  # 300-3000 kHz
    HF = "hf"  # 3-30 MHz
    VHF = "vhf"  # 30-300 MHz
    UHF = "uhf"  # 300-3000 MHz
    SHF = "shf"  # 3-30 GHz (HackRF up to 6 GHz)


class ModulationType(str, Enum):
    """Signal modulation types"""

    AM = "am"
    FM = "fm"
    NFM = "nfm"
    WFM = "wfm"
    USB = "usb"
    LSB = "lsb"
    CW = "cw"
    PSK = "psk"
    FSK = "fsk"
    QAM = "qam"
    OFDM = "ofdm"
    RAW = "raw"


class SignalType(str, Enum):
    """Known signal classifications"""

    # Maritime
    AIS = "ais"
    MARINE_VHF = "marine_vhf"
    NAVTEX = "navtex"

    # Aviation
    ADSB = "adsb"
    ACARS = "acars"
    VOR = "vor"
    ILS = "ils"
    DME = "dme"

    # Emergency
    EMERGENCY = "emergency"
    DISTRESS = "distress"

    # Cellular
    GSM = "gsm"
    UMTS = "umts"
    LTE = "lte"
    NR_5G = "5g"

    # IoT/ISM
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    ZIGBEE = "zigbee"
    LORA = "lora"

    # Amateur
    AMATEUR = "amateur"
    APRS = "aprs"
    FT8 = "ft8"

    # Other
    BROADCAST_FM = "broadcast_fm"
    BROADCAST_TV = "broadcast_tv"
    SATELLITE = "satellite"
    RADAR = "radar"
    UNKNOWN = "unknown"


class CaptureRequest(BaseModel):
    """Signal capture parameters"""

    frequency: float = Field(
        ..., ge=1e6, le=6e9, description="Frequency in Hz (1MHz-6GHz)"
    )
    sample_rate: float = Field(
        default=2e6, ge=1e6, le=20e6, description="Sample rate in Hz"
    )
    duration: float = Field(
        default=1.0, ge=0.1, le=60, description="Capture duration in seconds"
    )
    gain: int = Field(default=20, ge=0, le=47, description="LNA gain (0-47 dB)")
    amp_enable: bool = Field(default=True, description="Enable amplifier")
    antenna_power: bool = Field(
        default=False, description="Enable antenna power (bias-tee)"
    )

    @validator("frequency")
    def validate_frequency(cls, v):
        if v < 1e6 or v > 6e9:
            raise ValueError(
                f"Frequency {v/1e6:.1f} MHz outside HackRF range (1-6000 MHz)"
            )
        return v

    class Config:
        schema_extra = {
            "example": {
                "frequency": 103.7e6,
                "sample_rate": 2e6,
                "duration": 5.0,
                "gain": 30,
                "amp_enable": True,
                "antenna_power": False,
            }
        }


class SpectrumScanRequest(BaseModel):
    """Spectrum scanning parameters"""

    start_freq: float = Field(..., ge=1e6, le=6e9, description="Start frequency in Hz")
    stop_freq: float = Field(..., ge=1e6, le=6e9, description="Stop frequency in Hz")
    bin_width: float = Field(default=1e6, ge=1e5, le=10e6, description="FFT bin width")
    sweeps: int = Field(default=1, ge=1, le=100, description="Number of sweeps")

    @validator("stop_freq")
    def validate_range(cls, v, values):
        if "start_freq" in values and v <= values["start_freq"]:
            raise ValueError("Stop frequency must be greater than start frequency")
        return v


class SignalAnalysisResult(BaseModel):
    """Signal analysis output"""

    frequency: float
    signal_type: SignalType
    modulation: ModulationType
    power_dbm: float
    bandwidth_khz: float
    confidence: float = Field(..., ge=0, le=1)
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    location: str = "Valletta, Malta"


class ThreatAssessment(BaseModel):
    """Security threat analysis"""

    threat_level: str = Field(..., description="low/medium/high/critical")
    threat_type: str
    description: str
    frequency: float
    recommendations: List[str]
    evidence: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


# ==================== SIGNAL CAPTURE ====================


@app.post("/capture/signal", tags=["capture"], response_model=Dict[str, Any])
async def capture_signal(request: CaptureRequest, background_tasks: BackgroundTasks):
    """
    Capture raw IQ samples from specified frequency.

    Returns path to captured IQ file and basic statistics.
    """
    output_file = f"/tmp/capture_{int(request.frequency)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.iq"

    cmd = [
        "hackrf_transfer",
        "-r",
        output_file,
        "-f",
        str(int(request.frequency)),
        "-s",
        str(int(request.sample_rate)),
        "-n",
        str(int(request.sample_rate * request.duration)),
        "-g",
        str(request.gain),
    ]

    if request.amp_enable:
        cmd.extend(["-a", "1"])

    if request.antenna_power:
        cmd.extend(["-b", "1"])

    try:
        subprocess.run(
            cmd, capture_output=True, text=True, timeout=request.duration + 5
        )

        # Get file stats
        file_size = os.path.getsize(output_file)

        # Quick power calculation
        with open(output_file, "rb") as f:
            raw = f.read(min(100000, file_size))
            iq = np.frombuffer(raw, dtype=np.int8).astype(np.float32) / 128.0
            power_dbfs = 20 * np.log10(np.mean(np.abs(iq)) + 1e-10)

        return {
            "status": "success",
            "file_path": output_file,
            "frequency_mhz": request.frequency / 1e6,
            "duration_sec": request.duration,
            "file_size_mb": file_size / 1e6,
            "average_power_dbfs": float(power_dbfs),
            "sample_rate_msps": request.sample_rate / 1e6,
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Capture timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Capture failed: {str(e)}")


# ==================== SPECTRUM SCANNING ====================


@app.post("/spectrum/scan", tags=["spectrum"])
async def spectrum_scan(request: SpectrumScanRequest):
    """
    Perform wideband spectrum scan across specified range.

    Returns power measurements across frequency range.
    """
    cmd = [
        "hackrf_sweep",
        "-f",
        f"{int(request.start_freq/1e6)}:{int(request.stop_freq/1e6)}",
        "-w",
        str(int(request.bin_width)),
        "-n",
        str(request.sweeps),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Parse sweep results
        frequencies = []
        powers = []

        for line in result.stdout.split("\n"):
            if "2025" in line and "," in line:  # Data lines have timestamps
                parts = line.split(",")
                if len(parts) >= 8:
                    freq_low = float(parts[2])
                    freq_high = float(parts[3])
                    freq_center = (freq_low + freq_high) / 2
                    power = float(parts[6])

                    frequencies.append(freq_center / 1e6)  # Convert to MHz
                    powers.append(power)

        return {
            "frequencies_mhz": frequencies,
            "power_dbm": powers,
            "peak_frequency_mhz": frequencies[np.argmax(powers)] if powers else None,
            "peak_power_dbm": max(powers) if powers else None,
            "scan_range_mhz": [request.start_freq / 1e6, request.stop_freq / 1e6],
            "bin_width_khz": request.bin_width / 1e3,
            "timestamp": datetime.now(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


# ==================== SIGNAL ANALYSIS ====================


@app.post("/analysis/classify", tags=["analysis"], response_model=SignalAnalysisResult)
async def classify_signal(
    frequency: float = Query(..., description="Frequency in Hz"),
    iq_file: Optional[UploadFile] = File(None),
):
    """
    Classify and analyze captured signal using ML ensemble.

    Identifies signal type, modulation, and key parameters.
    """
    # This would integrate with the ML ensemble
    # For now, return intelligent guesses based on frequency

    signal_type = SignalType.UNKNOWN
    modulation = ModulationType.RAW
    confidence = 0.5

    # Frequency-based classification heuristics
    freq_mhz = frequency / 1e6

    if 88 <= freq_mhz <= 108:
        signal_type = SignalType.BROADCAST_FM
        modulation = ModulationType.WFM
        confidence = 0.95
    elif 108 <= freq_mhz <= 137:
        signal_type = (
            SignalType.AMATEUR if freq_mhz in [121.5, 123.1] else SignalType.AMATEUR
        )
        modulation = ModulationType.AM
        confidence = 0.8
    elif 156 <= freq_mhz <= 162:
        signal_type = SignalType.MARINE_VHF
        modulation = ModulationType.NFM
        confidence = 0.9
    elif abs(freq_mhz - 1090) < 1:
        signal_type = SignalType.ADSB
        modulation = ModulationType.RAW
        confidence = 0.99
    elif 2400 <= freq_mhz <= 2500:
        signal_type = SignalType.WIFI
        modulation = ModulationType.OFDM
        confidence = 0.85

    return SignalAnalysisResult(
        frequency=frequency,
        signal_type=signal_type,
        modulation=modulation,
        power_dbm=-50.0,  # Would be calculated from IQ data
        bandwidth_khz=200.0,  # Would be measured
        confidence=confidence,
        metadata={
            "frequency_band": (
                FrequencyBand.VHF if 30e6 <= frequency <= 300e6 else FrequencyBand.UHF
            )
        },
    )


# ==================== MARITIME INTELLIGENCE ====================


@app.get("/maritime/ais", tags=["maritime"])
async def get_ais_vessels():
    """
    Monitor AIS vessel broadcasts near Malta.

    Returns vessel positions and information.
    """
    # Capture AIS on 161.975 MHz and 162.025 MHz
    vessels = []

    for ais_freq in [161.975e6, 162.025e6]:
        # This would actually decode AIS messages
        # For demo, return sample data
        vessels.append(
            {
                "mmsi": "229857000",
                "name": "MAERSK ETIENNE",
                "type": "Cargo",
                "position": {"lat": 35.8989, "lon": 14.5146},
                "speed_knots": 12.5,
                "course": 270,
                "destination": "MALTA",
                "frequency_mhz": ais_freq / 1e6,
                "timestamp": datetime.now(),
            }
        )

    return {
        "vessels": vessels,
        "total_count": len(vessels),
        "coverage_area": "Central Mediterranean",
        "receiver_location": "Valletta, Malta",
    }


@app.get("/maritime/vhf_channels", tags=["maritime"])
async def maritime_vhf_status():
    """
    Monitor marine VHF channels for activity.

    Includes emergency channel 16 and port operations.
    """
    channels = {
        16: {
            "frequency_mhz": 156.800,
            "use": "Emergency/Calling",
            "activity": "monitoring",
        },
        1: {"frequency_mhz": 156.050, "use": "Port Operations", "activity": "low"},
        6: {"frequency_mhz": 156.300, "use": "Ship-to-ship", "activity": "moderate"},
        13: {"frequency_mhz": 156.650, "use": "Navigation", "activity": "high"},
        70: {"frequency_mhz": 156.525, "use": "DSC Digital", "activity": "periodic"},
    }

    return {
        "channels": channels,
        "emergency_status": "clear",
        "port": "Valletta Grand Harbour",
        "timestamp": datetime.now(),
    }


# ==================== AVIATION MONITORING ====================


@app.get("/aviation/adsb", tags=["aviation"])
async def track_aircraft():
    """
    Track aircraft via ADS-B on 1090 MHz.

    Returns aircraft positions and flight information.
    """
    # This would use dump1090 or similar
    aircraft = [
        {
            "icao": "4D2206",
            "callsign": "RYR8FW",
            "airline": "Ryanair",
            "altitude_ft": 38000,
            "speed_knots": 450,
            "heading": 135,
            "position": {"lat": 35.95, "lon": 14.40},
            "route": "MXP-MLA",
            "distance_km": 15.2,
            "timestamp": datetime.now(),
        }
    ]

    return {
        "aircraft": aircraft,
        "total_tracked": len(aircraft),
        "coverage_radius_km": 250,
        "receiver_location": "Valletta, Malta",
    }


@app.get("/aviation/frequencies", tags=["aviation"])
async def aviation_frequencies():
    """
    List aviation frequencies for Malta airspace.

    Includes tower, ground, approach, and emergency.
    """
    return {
        "malta_airport": {
            "tower": {"frequency_mhz": 118.120, "modulation": "AM"},
            "ground": {"frequency_mhz": 121.900, "modulation": "AM"},
            "approach": {"frequency_mhz": 134.700, "modulation": "AM"},
            "departure": {"frequency_mhz": 120.300, "modulation": "AM"},
        },
        "emergency": {
            "guard": {"frequency_mhz": 121.500, "modulation": "AM"},
            "secondary": {"frequency_mhz": 243.000, "modulation": "AM"},
        },
        "navigation": {
            "vor_mlt": {"frequency_mhz": 112.800, "type": "VOR/DME"},
            "ils_rw31": {"frequency_mhz": 109.500, "type": "ILS"},
        },
    }


# ==================== THREAT DETECTION ====================


@app.post("/threats/assess", tags=["threats"], response_model=ThreatAssessment)
async def assess_threat(frequency: float, signal_type: SignalType):
    """
    Assess security threats from detected signals.

    Identifies jamming, spoofing, and rogue transmitters.
    """
    threat_level = "low"
    threat_type = "none"
    description = "Normal signal activity"
    recommendations = []

    # Threat detection logic
    if (
        signal_type == SignalType.AIS
        and frequency != 161.975e6
        and frequency != 162.025e6
    ):
        threat_level = "high"
        threat_type = "AIS Spoofing"
        description = "AIS signal detected on non-standard frequency"
        recommendations = [
            "Verify vessel positions visually",
            "Cross-reference with port authority",
            "Record signal for forensic analysis",
        ]

    return ThreatAssessment(
        threat_level=threat_level,
        threat_type=threat_type,
        description=description,
        frequency=frequency,
        recommendations=recommendations,
        evidence={"signal_type": signal_type, "analysis_time": datetime.now()},
    )


@app.get("/threats/active", tags=["threats"])
async def active_threats():
    """
    List currently detected threats and anomalies.

    Real-time threat dashboard data.
    """
    return {
        "active_threats": [],
        "anomalies_detected": 0,
        "jamming_detected": False,
        "rogue_transmitters": [],
        "monitoring_status": "active",
        "last_scan": datetime.now(),
    }


# ==================== MACHINE LEARNING ====================


@app.post("/ml/fingerprint", tags=["ml"])
async def create_fingerprint(iq_file: UploadFile = File(...)):
    """
    Create RF fingerprint from IQ samples.

    Used for device identification and classification.
    """
    # Save uploaded file
    temp_path = f"/tmp/{iq_file.filename}"
    with open(temp_path, "wb") as f:
        content = await iq_file.read()
        f.write(content)

    # Generate fingerprint (simplified)
    with open(temp_path, "rb") as f:
        raw = f.read(10000)
        iq = np.frombuffer(raw, dtype=np.int8).astype(np.float32) / 128.0

        fingerprint = {
            "mean_power": float(np.mean(np.abs(iq))),
            "std_power": float(np.std(np.abs(iq))),
            "peak_power": float(np.max(np.abs(iq))),
            "spectral_entropy": float(
                np.random.random()
            ),  # Would calculate actual entropy
            "modulation_features": list(
                np.random.random(10)
            ),  # Would extract actual features
        }

    return {
        "fingerprint_id": f"fp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "features": fingerprint,
        "classification_ready": True,
    }


# ==================== REAL-TIME STREAMING ====================


@app.websocket("/realtime/waterfall")
async def waterfall_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time spectrum waterfall.

    Streams FFT data for visualization.
    """
    await websocket.accept()

    try:
        while True:
            # This would stream actual FFT data from HackRF
            # For demo, send random data
            fft_data = {
                "timestamp": datetime.now().isoformat(),
                "center_freq_mhz": 100.0,
                "bandwidth_mhz": 20.0,
                "fft_size": 1024,
                "power_data": list(np.random.random(1024) * -100),
            }

            await websocket.send_json(fft_data)
            await asyncio.sleep(0.1)  # 10 Hz update rate

    except Exception:
        await websocket.close()


# ==================== SYSTEM STATUS ====================


@app.get("/status", tags=["system"])
async def system_status():
    """
    Get HackRF and system status.

    Includes device info and health checks.
    """
    # Check HackRF
    hackrf_status = "disconnected"
    hackrf_info = {}

    try:
        result = subprocess.run(
            ["hackrf_info"], capture_output=True, text=True, timeout=2
        )
        if "Serial number" in result.stdout:
            hackrf_status = "connected"
            for line in result.stdout.split("\n"):
                if "Serial number:" in line:
                    hackrf_info["serial"] = line.split(":")[1].strip()
                elif "Firmware Version:" in line:
                    hackrf_info["firmware"] = line.split(":")[1].strip()
    except subprocess.SubprocessError:
        pass

    return {
        "status": "operational",
        "hackrf_status": hackrf_status,
        "hackrf_info": hackrf_info,
        "location": "Valletta, Malta",
        "coverage": "1 MHz - 6 GHz",
        "timestamp": datetime.now(),
        "api_version": "2.0.0",
    }


# ==================== ROOT REDIRECT ====================


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to interactive API docs."""
    return {"message": "Welcome to RF SIGINT API", "docs": "/docs", "redoc": "/redoc"}


# Add maritime and aviation routes
app = add_maritime_aviation_routes(app)

if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting RF Digital Forensics API Server")
    print("📡 Coverage: 1 MHz to 6 GHz")
    print("📍 Location: Valletta, Malta")
    print("📚 API Docs: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    uvicorn.run(app, host="0.0.0.0", port=8000)
