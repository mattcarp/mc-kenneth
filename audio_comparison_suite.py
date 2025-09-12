#!/usr/bin/env python3
"""
Audio Comparison Suite for ElevenLabs Pipeline
Visual spectrograms, objective metrics, and playback examples
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
from pathlib import Path
import tempfile
import subprocess
from scipy import signal
from scipy.fft import fft, fftfreq

sys.path.insert(0, 'src')
from audio_preprocessor import AudioPreprocessor

class AudioAnalyzer:
    """Analyze and compare audio quality with visual and objective metrics"""
    
    def __init__(self):
        self.preprocessor = AudioPreprocessor()
        
    def create_realistic_rf_capture(self, duration=10.0, save_path=None):
        """Create realistic RF voice capture with various noise types"""
        sample_rate = 22050
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        print(f"🎙️  Creating {duration:.1f}s RF voice simulation...")
        
        # Voice simulation (emergency maritime distress call)
        voice_segments = []
        
        # "Mayday, Mayday, this is vessel Alpha Bravo"
        for i, (freq, amplitude, mod_freq) in enumerate([
            (180, 0.4, 3.0),    # "Mayday"
            (185, 0.35, 2.8),   # "Mayday" 
            (175, 0.3, 3.2),    # "this is"
            (190, 0.4, 2.9),    # "vessel"
            (178, 0.35, 3.1),   # "Alpha Bravo"
        ]):
            start = i * duration / 5
            end = (i + 1) * duration / 5
            segment_t = t[(t >= start) & (t < end)]
            
            if len(segment_t) > 0:
                # Voice with harmonics
                voice = (np.sin(2 * np.pi * freq * segment_t) * amplitude +
                        np.sin(2 * np.pi * freq * 2.1 * segment_t) * amplitude * 0.6 +
                        np.sin(2 * np.pi * freq * 3.2 * segment_t) * amplitude * 0.3)
                
                # Voice characteristics
                voice *= (1 + 0.5 * np.sin(2 * np.pi * mod_freq * segment_t))  # Modulation
                voice *= np.exp(-0.05 * np.abs(segment_t - (start + end)/2))   # Envelope
                
                voice_segments.extend(voice)
            else:
                voice_segments.extend([0] * 1000)  # Silence
        
        # Ensure voice signal matches time array length
        if len(voice_segments) > len(t):
            voice_signal = np.array(voice_segments[:len(t)])
        else:
            voice_signal = np.pad(voice_segments, (0, len(t) - len(voice_segments)), mode='constant')
        voice_signal = np.array(voice_signal)
        
        # RF noise characteristics
        print("   Adding RF noise characteristics...")
        
        # 1. Atmospheric noise (white noise)
        atmospheric_noise = np.random.normal(0, 0.25, len(t))
        
        # 2. Equipment noise (pink noise - 1/f)
        white = np.random.normal(0, 1, len(t))
        pink_filter = signal.butter(1, 0.1, btype='low')
        pink_noise = signal.filtfilt(pink_filter[0], pink_filter[1], white) * 0.2
        
        # 3. Interference from other stations
        interference = np.sin(2 * np.pi * 1200 * t) * 0.15 * (np.sin(2 * np.pi * 0.3 * t) > 0.7)
        
        # 4. Static bursts (ignition interference)
        static_bursts = np.zeros_like(t)
        for burst_start in np.arange(1, duration-1, 2.3):
            burst_idx = int(burst_start * sample_rate)
            burst_len = int(0.1 * sample_rate)
            if burst_idx + burst_len < len(static_bursts):
                burst_noise = np.random.normal(0, 0.8, burst_len)
                static_bursts[burst_idx:burst_idx + burst_len] = burst_noise
        
        # 5. Analog transmission artifacts
        print("   Simulating analog transmission...")
        combined_signal = voice_signal + atmospheric_noise + pink_noise + interference + static_bursts
        
        # Analog saturation and filtering
        combined_signal = np.tanh(combined_signal * 1.3) * 0.85  # Soft clipping
        
        # Communications filter (300-3400 Hz passband)
        nyquist = sample_rate / 2
        low = 300 / nyquist
        high = 3400 / nyquist
        b, a = signal.butter(4, [low, high], btype='band')
        rf_audio = signal.filtfilt(b, a, combined_signal)
        
        if save_path:
            sf.write(save_path, rf_audio, sample_rate)
            print(f"   Saved: {save_path}")
            
        return rf_audio, sample_rate
    
    def analyze_audio_quality(self, original, processed, sample_rates, title="Audio Comparison"):
        """Comprehensive audio quality analysis with metrics and visualization"""
        
        print(f"\n📊 {title}")
        print("=" * 50)
        
        # Ensure same length for comparison
        min_len = min(len(original), len(processed))
        orig = original[:min_len]
        proc = processed[:min_len]
        
        orig_sr, proc_sr = sample_rates
        
        # Resample processed to match original if needed
        if orig_sr != proc_sr:
            from scipy.signal import resample
            proc = resample(proc, int(len(proc) * orig_sr / proc_sr))
            proc = proc[:len(orig)]  # Ensure same length after resampling
        
        # Objective Metrics
        print("🔍 Objective Quality Metrics:")
        
        # 1. Signal-to-Noise Ratio improvement
        orig_rms = np.sqrt(np.mean(orig**2))
        proc_rms = np.sqrt(np.mean(proc**2))
        
        # Estimate noise floor (bottom 10% of signal)
        orig_sorted = np.sort(np.abs(orig))
        proc_sorted = np.sort(np.abs(proc))
        orig_noise_floor = np.mean(orig_sorted[:len(orig_sorted)//10])
        proc_noise_floor = np.mean(proc_sorted[:len(proc_sorted)//10])
        
        if orig_noise_floor > 0 and proc_noise_floor > 0:
            snr_improvement = 20 * np.log10(orig_noise_floor / proc_noise_floor)
            print(f"   SNR Improvement: {snr_improvement:.1f} dB")
        
        # 2. Dynamic Range
        orig_dynamic_range = 20 * np.log10(np.max(np.abs(orig)) / max(orig_noise_floor, 1e-10))
        proc_dynamic_range = 20 * np.log10(np.max(np.abs(proc)) / max(proc_noise_floor, 1e-10))
        print(f"   Dynamic Range: {orig_dynamic_range:.1f} → {proc_dynamic_range:.1f} dB")
        
        # 3. RMS levels
        print(f"   RMS Level: {orig_rms:.4f} → {proc_rms:.4f}")
        
        # 4. Spectral analysis
        return self._create_spectral_comparison(orig, proc, orig_sr, title)
    
    def _create_spectral_comparison(self, original, processed, sample_rate, title):
        """Create visual spectral comparison"""
        
        plt.style.use('dark_background')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{title} - Spectral Analysis', fontsize=16, color='white')
        
        # Time domain comparison
        duration = len(original) / sample_rate
        t = np.linspace(0, duration, len(original))
        
        ax1.plot(t[:sample_rate*2], original[:sample_rate*2], color='red', alpha=0.7, linewidth=0.5)
        ax1.set_title('Original RF Audio (2s sample)', color='white')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Amplitude')
        ax1.grid(True, alpha=0.3)
        
        ax2.plot(t[:sample_rate*2], processed[:sample_rate*2], color='lime', alpha=0.7, linewidth=0.5)
        ax2.set_title('Processed Audio (2s sample)', color='white')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Amplitude')
        ax2.grid(True, alpha=0.3)
        
        # Frequency domain comparison
        freqs_orig = fftfreq(len(original), 1/sample_rate)
        fft_orig = np.abs(fft(original))
        
        freqs_proc = fftfreq(len(processed), 1/sample_rate)
        fft_proc = np.abs(fft(processed))
        
        # Plot positive frequencies only, up to 4kHz for voice analysis
        freq_mask = (freqs_orig >= 0) & (freqs_orig <= 4000)
        
        ax3.semilogy(freqs_orig[freq_mask], fft_orig[freq_mask], color='red', alpha=0.7)
        ax3.set_title('Original - Frequency Spectrum', color='white')
        ax3.set_xlabel('Frequency (Hz)')
        ax3.set_ylabel('Magnitude')
        ax3.grid(True, alpha=0.3)
        ax3.axvspan(300, 3400, alpha=0.2, color='yellow', label='Voice Band')
        ax3.legend()
        
        freq_mask_proc = (freqs_proc >= 0) & (freqs_proc <= 4000)
        ax4.semilogy(freqs_proc[freq_mask_proc], fft_proc[freq_mask_proc], color='lime', alpha=0.7)
        ax4.set_title('Processed - Frequency Spectrum', color='white')
        ax4.set_xlabel('Frequency (Hz)')
        ax4.set_ylabel('Magnitude')
        ax4.grid(True, alpha=0.3)
        ax4.axvspan(300, 3400, alpha=0.2, color='yellow', label='Voice Band')
        ax4.legend()
        
        plt.tight_layout()
        
        # Save the comparison
        comparison_path = Path(f"audio_comparison_{title.lower().replace(' ', '_')}.png")
        plt.savefig(comparison_path, dpi=150, bbox_inches='tight', facecolor='black')
        print(f"   📈 Spectral comparison saved: {comparison_path}")
        
        return comparison_path

def create_cli_player():
    """Create CLI audio player for quick comparisons"""
    
    player_script = """#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

def play_audio(file_path):
    try:
        # Try different audio players
        players = ['afplay', 'play', 'aplay', 'paplay']
        for player in players:
            try:
                subprocess.run([player, str(file_path)], check=True, 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"🔊 Playing: {file_path.name}")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        print("❌ No audio player found. Install sox or use system audio player.")
        return False
    except Exception as e:
        print(f"❌ Audio playback failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 play_audio.py <audio_file.wav>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    play_audio(file_path)
"""
    
    with open("play_audio.py", "w") as f:
        f.write(player_script)
    
    # Make executable
    subprocess.run(['chmod', '+x', 'play_audio.py'])
    print("✅ Created CLI audio player: play_audio.py")

def main():
    """Comprehensive audio comparison demonstration"""
    print("🎧 ElevenLabs Audio Comparison Suite")
    print("=" * 60)
    
    analyzer = AudioAnalyzer()
    
    # Create realistic RF audio examples
    original_path = Path("rf_original.wav")
    processed_path = Path("rf_processed.wav")
    
    # Generate original RF audio
    original_audio, sample_rate = analyzer.create_realistic_rf_capture(
        duration=8.0, save_path=original_path
    )
    
    # Process through our pipeline (preprocessing only)
    print(f"\n🔧 Processing through audio pipeline...")
    processed_file = analyzer.preprocessor.process_file(original_path, processed_path)
    processed_audio, processed_sr = sf.read(processed_file)
    
    # Comprehensive analysis
    comparison_image = analyzer.analyze_audio_quality(
        original_audio, processed_audio, 
        (sample_rate, processed_sr),
        "RF Voice Processing Pipeline"
    )
    
    # Create CLI player
    create_cli_player()
    
    print(f"\n🎉 Audio Comparison Complete!")
    print(f"📁 Files created:")
    print(f"   🎵 Original RF: {original_path}")
    print(f"   🎵 Processed: {processed_path}")
    print(f"   📊 Visual comparison: {comparison_image}")
    print(f"   🔧 CLI player: play_audio.py")
    
    print(f"\n🎧 To listen:")
    print(f"   python3 play_audio.py {original_path}")
    print(f"   python3 play_audio.py {processed_path}")
    
    print(f"\n📊 To view spectral analysis:")
    print(f"   open {comparison_image}")
    
    return original_path, processed_path, comparison_image

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Audio comparison interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)