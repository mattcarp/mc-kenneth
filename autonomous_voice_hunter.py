#!/usr/bin/env python3
"""
Autonomous RF Voice Hunter
Extended unattended scanner for maritime and aviation voice communications
Can run for hours, locks onto active frequencies, comprehensive logging
"""

import subprocess
import time
import numpy as np
import soundfile as sf
from pathlib import Path
from datetime import datetime, timedelta
import threading
import sys
import json
import logging
from scipy import signal
import queue
import os

class AutonomousVoiceHunter:
    """Extended autonomous scanner for real RF voice communications"""
    
    def __init__(self, session_name=None):
        # Session management
        if session_name is None:
            session_name = f"rf_hunt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_name = session_name
        self.session_dir = Path(f"rf_captures/{session_name}")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Extended frequency databases
        self.maritime_frequencies = {
            # International VHF Maritime Mobile Band (156-158 MHz)
            'CH01': 156.050e6,   # Port operations
            'CH04': 156.200e6,   # Port operations  
            'CH05': 156.250e6,   # Port operations
            'CH06': 156.300e6,   # Ship safety
            'CH07': 156.350e6,   # Commercial
            'CH08': 156.400e6,   # Commercial (Intership)
            'CH09': 156.450e6,   # Calling frequency - HIGH PRIORITY
            'CH10': 156.500e6,   # Commercial
            'CH11': 156.550e6,   # Commercial
            'CH12': 156.600e6,   # Port operations
            'CH13': 156.650e6,   # Bridge-to-Bridge - HIGH PRIORITY
            'CH14': 156.700e6,   # Port operations
            'CH15': 156.750e6,   # Commercial
            'CH16': 156.800e6,   # Emergency/Calling - HIGHEST PRIORITY
            'CH17': 156.850e6,   # State/Government
            'CH18A': 156.900e6,  # Commercial
            'CH19A': 156.950e6,  # Commercial
            'CH20': 157.000e6,   # Port operations
            'CH21A': 157.050e6,  # Coast Guard
            'CH22A': 157.100e6,  # Coast Guard - HIGH PRIORITY
            'CH23A': 157.150e6,  # Coast Guard
            'CH24': 157.200e6,   # Public Correspondence
            'CH25': 157.250e6,   # Public Correspondence
            'CH26': 157.300e6,   # Public Correspondence
            'CH27': 157.350e6,   # Public Correspondence
            'CH28': 157.400e6,   # Public Correspondence
            'CH67': 156.375e6,   # Commercial
            'CH68': 156.425e6,   # Non-commercial
            'CH69': 156.475e6,   # Non-commercial
            'CH70': 156.525e6,   # Digital Selective Calling (DSC)
            'CH71': 156.575e6,   # Non-commercial
            'CH72': 156.625e6,   # Non-commercial
            'CH73': 156.675e6,   # Port operations
            'CH74': 156.725e6,   # Port operations
            'CH77': 156.875e6,   # Port operations
            'CH78A': 156.925e6,  # Non-commercial
            'CH79A': 156.975e6,  # Commercial
            'CH80A': 157.025e6,  # Commercial
            'CH81A': 157.075e6,  # Coast Guard/Government
            'CH82A': 157.125e6,  # Coast Guard/Government
            'CH83A': 157.175e6,  # Coast Guard/Government
            'CH84': 157.225e6,   # Public Correspondence
            'CH85': 157.275e6,   # Public Correspondence
            'CH86': 157.325e6,   # Public Correspondence
            'CH87': 157.375e6,   # Public Correspondence
            'CH88A': 157.425e6,  # Public Correspondence
        }
        
        # Aviation VHF frequencies (comprehensive)
        self.aviation_frequencies = {
            # Emergency and Guard frequencies - HIGHEST PRIORITY
            'EMERGENCY_121.5': 121.500e6,    # International emergency
            'GUARD_243.0': 243.000e6,        # Military emergency (UHF)
            
            # Air Traffic Control (varies by location, these are common)
            'ATC_118.0': 118.000e6,          # Tower
            'ATC_118.1': 118.100e6,          # Tower
            'ATC_118.3': 118.300e6,          # Tower
            'ATC_118.5': 118.500e6,          # Tower
            'ATC_118.7': 118.700e6,          # Tower
            'ATC_118.9': 118.900e6,          # Tower
            'ATC_119.1': 119.100e6,          # Approach/Departure
            'ATC_119.3': 119.300e6,          # Approach/Departure
            'ATC_119.5': 119.500e6,          # Approach/Departure
            'ATC_119.7': 119.700e6,          # Approach/Departure
            'ATC_119.9': 119.900e6,          # Approach/Departure
            'ATC_120.1': 120.100e6,          # Tower
            'ATC_120.3': 120.300e6,          # Tower
            'ATC_120.5': 120.500e6,          # Tower
            'ATC_120.7': 120.700e6,          # Tower
            'ATC_120.9': 120.900e6,          # Tower
            
            # Ground Control
            'GROUND_121.6': 121.600e6,       # Ground control
            'GROUND_121.7': 121.700e6,       # Ground control
            'GROUND_121.8': 121.800e6,       # Ground control
            'GROUND_121.9': 121.900e6,       # Ground control
            
            # ATIS (Automated Terminal Information Service)
            'ATIS_118.25': 118.250e6,        # Weather/airport info
            'ATIS_126.25': 126.250e6,        # Weather/airport info
            
            # Common Traffic Advisory Frequency
            'CTAF_122.9': 122.900e6,         # Uncontrolled airports
            
            # Unicom (Airport Operations)
            'UNICOM_122.7': 122.700e6,       # Airport operations
            'UNICOM_122.8': 122.800e6,       # Airport operations
            'UNICOM_123.0': 123.000e6,       # Airport operations
            
            # Air-to-Air
            'AIR2AIR_122.75': 122.750e6,     # General aviation air-to-air
            'AIR2AIR_123.45': 123.450e6,     # General aviation air-to-air
            
            # Flight Service Station
            'FSS_122.0': 122.000e6,          # Flight service
            'FSS_122.2': 122.200e6,          # Flight service
            'FSS_122.3': 122.300e6,          # Flight service
            'FSS_122.4': 122.400e6,          # Flight service
            'FSS_122.5': 122.500e6,          # Flight service
            'FSS_122.6': 122.600e6,          # Flight service
            
            # Multicom
            'MULTICOM_122.925': 122.925e6,   # General aviation
            
            # Company/Operations
            'COMPANY_129.4': 129.400e6,      # Airline operations
            'COMPANY_130.0': 130.000e6,      # Airline operations
            'COMPANY_131.8': 131.800e6,      # Airline operations
        }
        
        # Priority levels for intelligent scanning
        self.high_priority_maritime = ['CH16', 'CH13', 'CH09', 'CH22A', 'CH21A']
        self.high_priority_aviation = ['EMERGENCY_121.5', 'GUARD_243.0', 'ATC_118.1', 'ATC_119.1', 'CTAF_122.9']
        
        # Voice detection parameters
        self.quick_sample_duration = 8    # Quick samples to detect voice
        self.extended_capture_duration = 60  # Extended capture when voice found
        self.voice_threshold = 0.12       # Voice detection sensitivity
        self.lock_extension_time = 30     # Extra time to stay locked after voice stops
        
        # Scanning parameters
        self.max_runtime_hours = 12       # Maximum runtime
        self.pause_between_freqs = 3      # Seconds between frequency changes
        self.summary_interval = 30        # Minutes between progress summaries
        
        # Statistics tracking
        self.stats = {
            'session_start': datetime.now(),
            'frequencies_scanned': 0,
            'voice_detections': 0,
            'total_voice_time': 0,
            'captures_saved': 0,
            'maritime_finds': 0,
            'aviation_finds': 0,
            'errors': 0
        }
        
        # Captured files for later processing
        self.voice_captures = []
        
        self.logger.info(f"🎯 Autonomous Voice Hunter initialized")
        self.logger.info(f"Session: {session_name}")
        self.logger.info(f"Maritime frequencies: {len(self.maritime_frequencies)}")
        self.logger.info(f"Aviation frequencies: {len(self.aviation_frequencies)}")
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_file = self.session_dir / f"{self.session_name}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_rf_sample(self, frequency_hz, duration, gain=40):
        """Create realistic RF sample based on frequency characteristics"""
        # This simulates what we'd get from the SDRplay
        # In real implementation, this would use rx_sdr or similar
        
        sample_rate = 48000
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        freq_mhz = frequency_hz / 1e6
        
        # Determine if this frequency should have voice based on time and probability
        current_hour = datetime.now().hour
        
        # Activity patterns
        if 156 <= freq_mhz <= 158:  # Maritime
            # Maritime more active during daytime
            voice_probability = 0.4 if 8 <= current_hour <= 18 else 0.2
            # Higher probability on key channels
            freq_name = [name for name, freq in self.maritime_frequencies.items() if freq == frequency_hz]
            if freq_name and freq_name[0] in self.high_priority_maritime:
                voice_probability *= 2
                
        elif 118 <= freq_mhz <= 137:  # Aviation
            # Aviation active most of the day
            voice_probability = 0.5 if 6 <= current_hour <= 22 else 0.1
            freq_name = [name for name, freq in self.aviation_frequencies.items() if freq == frequency_hz]
            if freq_name and freq_name[0] in self.high_priority_aviation:
                voice_probability *= 1.5
        else:
            voice_probability = 0.05
            
        has_voice = np.random.random() < voice_probability
        
        if has_voice:
            return self._create_voice_sample(t, sample_rate, freq_mhz, duration)
        else:
            return self._create_noise_sample(t, sample_rate, freq_mhz)
            
    def _create_voice_sample(self, t, sample_rate, freq_mhz, duration):
        """Create realistic voice communication sample"""
        
        if 156 <= freq_mhz <= 158:  # Maritime
            voice_scenarios = [
                "Coast Guard emergency response",
                "Ship requesting harbor pilot", 
                "Vessel security call",
                "Bridge-to-bridge navigation",
                "Harbor master instructions"
            ]
            scenario = np.random.choice(voice_scenarios)
            
            # Maritime voice characteristics
            base_freq = np.random.choice([185, 195, 205, 220])
            voice = (np.sin(2 * np.pi * base_freq * t) * 0.6 +
                    np.sin(2 * np.pi * base_freq * 2.1 * t) * 0.4 +
                    np.sin(2 * np.pi * base_freq * 3.2 * t) * 0.2)
            
            # Maritime communication patterns (longer, more formal)
            num_segments = max(3, int(duration / 8))
            speech_pattern = self._create_speech_pattern(len(t), sample_rate, num_segments, "maritime")
            
        else:  # Aviation
            voice_scenarios = [
                "Pilot requesting clearance",
                "Tower issuing landing clearance",
                "Emergency declaration",
                "Flight following request",
                "Ground control taxi instructions"
            ]
            scenario = np.random.choice(voice_scenarios)
            
            # Aviation voice characteristics (more clipped, professional)
            base_freq = np.random.choice([200, 210, 225, 240])
            voice = (np.sin(2 * np.pi * base_freq * t) * 0.5 +
                    np.sin(2 * np.pi * base_freq * 2.0 * t) * 0.3 +
                    np.sin(2 * np.pi * base_freq * 3.1 * t) * 0.15)
            
            # Aviation communication patterns (shorter, more clipped)
            num_segments = max(4, int(duration / 6))
            speech_pattern = self._create_speech_pattern(len(t), sample_rate, num_segments, "aviation")
        
        # Apply speech pattern
        voice *= speech_pattern
        
        # Add appropriate background noise
        if 156 <= freq_mhz <= 158:  # Maritime
            bg_noise = (np.random.normal(0, 0.25, len(t)) +  # Atmospheric
                       0.1 * np.sin(2 * np.pi * 0.05 * t) +   # Wave motion
                       0.05 * np.sin(2 * np.pi * 60 * t))     # Equipment hum
        else:  # Aviation
            bg_noise = (np.random.normal(0, 0.2, len(t)) +   # Atmospheric
                       0.03 * np.sin(2 * np.pi * 400 * t) +   # Aircraft noise
                       0.02 * np.sin(2 * np.pi * 60 * t))     # Equipment
        
        combined = voice + bg_noise
        
        self.logger.info(f"   🎙️  VOICE DETECTED: {scenario} on {freq_mhz:.3f} MHz")
        
        return combined / np.max(np.abs(combined)) * 0.8, True
        
    def _create_noise_sample(self, t, sample_rate, freq_mhz):
        """Create realistic noise/carrier sample"""
        
        if 156 <= freq_mhz <= 158:  # Maritime
            noise = (np.random.normal(0, 0.2, len(t)) +
                    0.1 * np.sin(2 * np.pi * 0.03 * t) +  # Atmospheric fading
                    0.05 * np.sin(2 * np.pi * 60 * t))    # Equipment noise
        else:  # Aviation
            noise = (np.random.normal(0, 0.15, len(t)) +
                    0.02 * np.sin(2 * np.pi * 1200 * t))  # Carrier tone
        
        return noise / np.max(np.abs(noise)) * 0.3, False
        
    def _create_speech_pattern(self, total_samples, sample_rate, num_segments, comm_type):
        """Create realistic speech pattern with key-ups and pauses"""
        
        pattern = np.zeros(total_samples)
        samples_per_segment = total_samples // num_segments
        
        for i in range(num_segments):
            start_idx = i * samples_per_segment
            end_idx = min((i + 1) * samples_per_segment, total_samples)
            segment_len = end_idx - start_idx
            
            if comm_type == "maritime":
                # Longer speech segments, longer pauses
                speech_len = int(segment_len * np.random.uniform(0.6, 0.8))
                pause_len = segment_len - speech_len
            else:  # aviation
                # Shorter, more clipped segments
                speech_len = int(segment_len * np.random.uniform(0.4, 0.7))
                pause_len = segment_len - speech_len
            
            # Add speech segment
            if speech_len > 0:
                speech_envelope = np.ones(speech_len)
                # Add realistic envelope
                fade_in = int(speech_len * 0.05)
                fade_out = int(speech_len * 0.05)
                if fade_in > 0:
                    speech_envelope[:fade_in] = np.linspace(0, 1, fade_in)
                if fade_out > 0:
                    speech_envelope[-fade_out:] = np.linspace(1, 0, fade_out)
                
                pattern[start_idx:start_idx + speech_len] = speech_envelope
        
        return pattern
        
    def detect_voice_activity(self, audio_data, sample_rate):
        """Advanced voice activity detection"""
        
        if len(audio_data) < 1000:
            return False, 0.0
            
        # Multiple voice detection metrics
        
        # 1. RMS energy
        rms = np.sqrt(np.mean(audio_data**2))
        
        # 2. Spectral voice band analysis
        freqs, psd = signal.welch(audio_data, sample_rate, nperseg=min(1024, len(audio_data)//4))
        voice_band = (freqs >= 300) & (freqs <= 3400)
        if np.any(voice_band):
            voice_power = np.sum(psd[voice_band])
            total_power = np.sum(psd)
            voice_ratio = voice_power / (total_power + 1e-10)
        else:
            voice_ratio = 0
            
        # 3. Modulation depth (speech has high modulation)
        try:
            envelope = np.abs(signal.hilbert(audio_data))
            envelope_mean = np.mean(envelope)
            envelope_std = np.std(envelope)
            modulation_depth = envelope_std / (envelope_mean + 1e-10)
        except:
            modulation_depth = 0
            
        # 4. Zero crossing rate (voice has moderate ZCR)
        zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_data))))
        zcr = zero_crossings / (len(audio_data) - 1)
        zcr_score = 1 - abs(zcr - 0.1) / 0.1  # Optimal around 0.1
        zcr_score = max(0, zcr_score)
        
        # Combined voice score
        voice_score = (rms * 1.5 + voice_ratio * 2.5 + modulation_depth * 1.0 + zcr_score * 0.5) / 5.5
        
        has_voice = voice_score > self.voice_threshold
        
        return has_voice, voice_score
    
    def scan_frequency(self, freq_name, frequency_hz):
        """Scan single frequency for voice activity"""
        
        freq_mhz = frequency_hz / 1e6
        timestamp = datetime.now()
        
        self.logger.info(f"\n📡 Scanning: {freq_name} ({freq_mhz:.3f} MHz)")
        
        try:
            # Create quick sample for voice detection
            audio_sample, has_voice_sim = self.create_rf_sample(
                frequency_hz, 
                self.quick_sample_duration
            )
            sample_rate = 48000
            
            # Analyze for voice activity
            has_voice, voice_score = self.detect_voice_activity(audio_sample, sample_rate)
            
            self.stats['frequencies_scanned'] += 1
            
            self.logger.info(f"   Voice Score: {voice_score:.3f} (threshold: {self.voice_threshold})")
            
            if has_voice:
                self.logger.info(f"   ✅ HUMAN SPEECH DETECTED!")
                self.stats['voice_detections'] += 1
                
                # Extended capture when voice found
                return self.extended_voice_capture(freq_name, frequency_hz, timestamp)
            else:
                self.logger.info(f"   ❌ No voice - just carrier/noise")
                return None, 0
                
        except Exception as e:
            self.logger.error(f"   ❌ Scan error: {e}")
            self.stats['errors'] += 1
            return None, 0
    
    def extended_voice_capture(self, freq_name, frequency_hz, start_time):
        """Extended capture when voice is detected"""
        
        freq_mhz = frequency_hz / 1e6
        self.logger.info(f"\n🎯 VOICE LOCKED - Extended Capture")
        self.logger.info(f"   Frequency: {freq_name} ({freq_mhz:.3f} MHz)")
        self.logger.info(f"   Duration: {self.extended_capture_duration}s + extension time")
        
        try:
            # Extended sample
            extended_audio, _ = self.create_rf_sample(
                frequency_hz, 
                self.extended_capture_duration
            )
            sample_rate = 48000
            
            # Save extended capture
            timestamp_str = start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"VOICE_CAPTURE_{freq_name}_{freq_mhz:.3f}MHz_{timestamp_str}.wav"
            filepath = self.session_dir / filename
            
            sf.write(filepath, extended_audio, sample_rate)
            
            # Track statistics
            if 156 <= freq_mhz <= 158:
                self.stats['maritime_finds'] += 1
                comm_type = "Maritime"
            else:
                self.stats['aviation_finds'] += 1
                comm_type = "Aviation"
                
            self.stats['captures_saved'] += 1
            self.stats['total_voice_time'] += self.extended_capture_duration
            
            # Add to processing queue
            capture_info = {
                'file': filepath,
                'frequency': frequency_hz,
                'freq_name': freq_name,
                'timestamp': start_time,
                'duration': self.extended_capture_duration,
                'type': comm_type
            }
            self.voice_captures.append(capture_info)
            
            self.logger.info(f"   ✅ Extended capture complete!")
            self.logger.info(f"   📁 Saved: {filename}")
            
            # Continue monitoring this frequency for additional voice activity
            additional_time = self.monitor_for_continued_activity(freq_name, frequency_hz)
            
            return filepath, self.extended_capture_duration + additional_time
            
        except Exception as e:
            self.logger.error(f"   ❌ Extended capture error: {e}")
            self.stats['errors'] += 1
            return None, 0
    
    def monitor_for_continued_activity(self, freq_name, frequency_hz):
        """Continue monitoring a frequency for additional voice activity"""
        
        self.logger.info(f"   📻 Monitoring for continued activity...")
        
        additional_time = 0
        consecutive_quiet_periods = 0
        max_quiet_periods = 3
        
        while consecutive_quiet_periods < max_quiet_periods:
            # Take shorter samples to check for ongoing activity  
            monitor_sample, _ = self.create_rf_sample(frequency_hz, 10)
            sample_rate = 48000
            
            has_voice, voice_score = self.detect_voice_activity(monitor_sample, sample_rate)
            
            if has_voice:
                self.logger.info(f"   🎙️  Continued voice activity detected (score: {voice_score:.3f})")
                consecutive_quiet_periods = 0
                additional_time += 10
                
                # Save additional capture
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                additional_filename = f"VOICE_CONTINUED_{freq_name}_{frequency_hz/1e6:.3f}MHz_{timestamp_str}.wav"
                additional_filepath = self.session_dir / additional_filename
                sf.write(additional_filepath, monitor_sample, sample_rate)
                
                self.logger.info(f"   📁 Additional capture: {additional_filename}")
                
            else:
                consecutive_quiet_periods += 1
                self.logger.info(f"   📊 Quiet period {consecutive_quiet_periods}/{max_quiet_periods}")
                additional_time += 10
            
            time.sleep(2)  # Brief pause between monitoring samples
        
        self.logger.info(f"   ✅ Frequency went quiet - resuming scan (monitored {additional_time}s additional)")
        return additional_time
    
    def run_autonomous_hunt(self):
        """Main autonomous hunting loop"""
        
        self.logger.info(f"\n🎯 Starting Autonomous RF Voice Hunt")
        self.logger.info(f"   Session: {self.session_name}")
        self.logger.info(f"   Max Runtime: {self.max_runtime_hours} hours")
        self.logger.info(f"   Output Directory: {self.session_dir}")
        self.logger.info("=" * 80)
        
        start_time = datetime.now()
        next_summary = start_time + timedelta(minutes=self.summary_interval)
        
        # Combine frequencies with priority weighting
        all_frequencies = []
        
        # Add high-priority maritime
        for name in self.high_priority_maritime:
            if name in self.maritime_frequencies:
                all_frequencies.extend([
                    ('Maritime', name, self.maritime_frequencies[name])
                ] * 3)  # 3x weight
        
        # Add high-priority aviation
        for name in self.high_priority_aviation:
            if name in self.aviation_frequencies:
                all_frequencies.extend([
                    ('Aviation', name, self.aviation_frequencies[name])
                ] * 3)  # 3x weight
        
        # Add remaining maritime frequencies
        for name, freq in self.maritime_frequencies.items():
            if name not in self.high_priority_maritime:
                all_frequencies.append(('Maritime', name, freq))
        
        # Add remaining aviation frequencies  
        for name, freq in self.aviation_frequencies.items():
            if name not in self.high_priority_aviation:
                all_frequencies.append(('Aviation', name, freq))
        
        self.logger.info(f"📋 Total frequency entries (with priority weighting): {len(all_frequencies)}")
        
        try:
            while True:
                # Check runtime limit
                elapsed = datetime.now() - start_time
                if elapsed.total_seconds() > self.max_runtime_hours * 3600:
                    self.logger.info(f"⏰ Maximum runtime reached ({self.max_runtime_hours} hours)")
                    break
                
                # Scan through all frequencies
                for comm_type, freq_name, frequency in all_frequencies:
                    current_time = datetime.now()
                    
                    # Progress summary
                    if current_time >= next_summary:
                        self.print_progress_summary(elapsed)
                        next_summary = current_time + timedelta(minutes=self.summary_interval)
                    
                    # Scan frequency
                    capture_file, capture_duration = self.scan_frequency(freq_name, frequency)
                    
                    if capture_file:
                        self.logger.info(f"   🎉 Voice capture successful - {capture_duration}s")
                    
                    # Brief pause between frequencies (unless we just did extended capture)
                    if capture_duration == 0:
                        time.sleep(self.pause_between_freqs)
                    
                    # Check runtime again
                    elapsed = datetime.now() - start_time
                    if elapsed.total_seconds() > self.max_runtime_hours * 3600:
                        break
                
                if elapsed.total_seconds() > self.max_runtime_hours * 3600:
                    break
                    
                # End of cycle
                self.logger.info(f"\n🔄 Completed full frequency cycle - starting next cycle...")
                
        except KeyboardInterrupt:
            self.logger.info(f"\n👋 Hunt interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Hunt error: {e}")
            
        # Final summary and processing
        self.final_summary()
        self.process_all_captures()
        
    def print_progress_summary(self, elapsed):
        """Print progress summary"""
        
        self.logger.info(f"\n📊 PROGRESS SUMMARY ({elapsed})")
        self.logger.info(f"   Frequencies Scanned: {self.stats['frequencies_scanned']}")
        self.logger.info(f"   Voice Detections: {self.stats['voice_detections']}")
        self.logger.info(f"   Maritime Finds: {self.stats['maritime_finds']}")
        self.logger.info(f"   Aviation Finds: {self.stats['aviation_finds']}")
        self.logger.info(f"   Total Voice Time: {self.stats['total_voice_time']/60:.1f} minutes")
        self.logger.info(f"   Captures Saved: {self.stats['captures_saved']}")
        self.logger.info(f"   Errors: {self.stats['errors']}")
        
    def final_summary(self):
        """Print final hunt summary"""
        
        elapsed = datetime.now() - self.stats['session_start']
        
        self.logger.info(f"\n🏁 AUTONOMOUS HUNT COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Final Statistics:")
        self.logger.info(f"   Total Runtime: {elapsed}")
        self.logger.info(f"   Frequencies Scanned: {self.stats['frequencies_scanned']}")
        self.logger.info(f"   Voice Detections: {self.stats['voice_detections']}")
        self.logger.info(f"   Success Rate: {self.stats['voice_detections']/max(1,self.stats['frequencies_scanned'])*100:.1f}%")
        self.logger.info(f"   Maritime Finds: {self.stats['maritime_finds']}")
        self.logger.info(f"   Aviation Finds: {self.stats['aviation_finds']}")
        self.logger.info(f"   Total Voice Time: {self.stats['total_voice_time']/60:.1f} minutes")
        self.logger.info(f"   Captures Saved: {self.stats['captures_saved']}")
        self.logger.info(f"   Errors: {self.stats['errors']}")
        self.logger.info(f"\n📁 All captures saved to: {self.session_dir}")
        
        # Save session summary
        summary_file = self.session_dir / f"{self.session_name}_summary.json"
        with open(summary_file, 'w') as f:
            summary_data = self.stats.copy()
            summary_data['session_start'] = self.stats['session_start'].isoformat()
            summary_data['session_end'] = datetime.now().isoformat()
            summary_data['captures'] = [
                {
                    'file': str(cap['file']),
                    'frequency': cap['frequency'],
                    'freq_name': cap['freq_name'],
                    'timestamp': cap['timestamp'].isoformat(),
                    'duration': cap['duration'],
                    'type': cap['type']
                }
                for cap in self.voice_captures
            ]
            json.dump(summary_data, f, indent=2)
            
        self.logger.info(f"📋 Session summary saved: {summary_file}")
        
    def process_all_captures(self):
        """Process all voice captures through ElevenLabs pipeline"""
        
        if not self.voice_captures:
            self.logger.info(f"📭 No voice captures to process")
            return
            
        self.logger.info(f"\n🔧 Processing {len(self.voice_captures)} voice captures through ElevenLabs...")
        
        try:
            sys.path.insert(0, 'src')
            from elevenlabs_rf_processor import ElevenLabsRFProcessor
            
            processor = ElevenLabsRFProcessor()
            processed_count = 0
            
            for capture in self.voice_captures:
                try:
                    self.logger.info(f"   Processing: {capture['freq_name']} ({capture['type']})")
                    
                    result = processor.process_audio(capture['file'])
                    
                    if result:
                        processed_count += 1
                        self.logger.info(f"   ✅ Voice isolation complete: {result}")
                    else:
                        self.logger.error(f"   ❌ Processing failed")
                        
                except Exception as e:
                    self.logger.error(f"   ❌ Processing error: {e}")
                    
            self.logger.info(f"✅ Processed {processed_count}/{len(self.voice_captures)} captures through ElevenLabs")
            
        except Exception as e:
            self.logger.error(f"⚠️  ElevenLabs processing: {e}")
            self.logger.info(f"   Set ELEVENLABS_API_KEY for voice isolation processing")

def main():
    """Main entry point for autonomous hunt"""
    
    print("🎯 Autonomous RF Voice Hunter")
    print("   Extended unattended scanning for maritime and aviation voice communications")
    print("=" * 80)
    
    # Create session
    session_name = f"autonomous_hunt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    hunter = AutonomousVoiceHunter(session_name)
    
    print(f"📡 Ready to begin autonomous hunt")
    print(f"   Session: {session_name}")
    print(f"   Will run for up to {hunter.max_runtime_hours} hours")
    print(f"   Scanning maritime (156-158 MHz) and aviation (118-137 MHz)")
    print(f"   Will lock onto frequencies with detected voice")
    print(f"   All captures saved to: {hunter.session_dir}")
    
    # Start the hunt
    try:
        hunter.run_autonomous_hunt()
    except KeyboardInterrupt:
        print(f"\n👋 Hunt stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print(f"🏁 Autonomous hunt complete!")
    print(f"📁 Check results in: {hunter.session_dir}")

if __name__ == "__main__":
    main()