#!/usr/bin/env python3
"""
Sample Validator - Quick verification of top voice detection results
Plays and analyzes a few samples to confirm detection quality
"""

import soundfile as sf
import numpy as np
from pathlib import Path
import subprocess
import time

def analyze_sample(audio_file):
    """Quick analysis of a sample file"""
    
    try:
        audio, sample_rate = sf.read(str(audio_file))
        
        duration = len(audio) / sample_rate
        rms = np.sqrt(np.mean(audio**2))
        
        # Quick spectral check
        if len(audio) > 1024:
            fft_result = np.abs(np.fft.fft(audio[:1024]))
            freqs = np.fft.fftfreq(1024, 1/sample_rate)
            
            voice_mask = (freqs >= 300) & (freqs <= 3400) & (freqs >= 0)
            total_mask = freqs >= 0
            
            voice_energy = np.sum(fft_result[voice_mask])
            total_energy = np.sum(fft_result[total_mask])
            voice_ratio = voice_energy / total_energy if total_energy > 0 else 0
        else:
            voice_ratio = 0
        
        return {
            'duration': duration,
            'rms': rms,
            'voice_ratio': voice_ratio,
            'peak_amplitude': np.max(np.abs(audio)),
            'dynamic_range': np.max(audio) - np.min(audio)
        }
        
    except Exception as e:
        return {'error': str(e)}

def validate_top_samples():
    """Validate top voice detection results"""
    
    print("🔍 Sample Validator - Checking Top Voice Detections")
    print("=" * 60)
    
    capture_dir = Path("rf_captures/autonomous_hunt_20250911_212457")
    
    # Get top files from batch 1
    batch_file = "elevenlabs_batch_01.txt"
    
    if not Path(batch_file).exists():
        print("❌ Batch file not found. Run elevenlabs_batch_organizer.py first.")
        return
    
    with open(batch_file, 'r') as f:
        lines = [line.strip() for line in f.readlines() if not line.startswith('#') and line.strip()]
    
    print(f"📊 Analyzing top {min(5, len(lines))} files from Batch 1...")
    
    for i, filename in enumerate(lines[:5]):
        print(f"\n🎵 Sample {i+1}: {filename}")
        
        audio_path = capture_dir / filename
        
        if not audio_path.exists():
            print(f"   ❌ File not found: {audio_path}")
            continue
        
        # Analyze
        analysis = analyze_sample(audio_path)
        
        if 'error' in analysis:
            print(f"   ❌ Analysis error: {analysis['error']}")
            continue
        
        print(f"   📊 Duration: {analysis['duration']:.1f}s")
        print(f"   📊 RMS Energy: {analysis['rms']:.3f}")
        print(f"   📊 Voice Ratio: {analysis['voice_ratio']:.3f}")
        print(f"   📊 Dynamic Range: {analysis['dynamic_range']:.3f}")
        
        # Quality assessment
        quality_score = 0
        reasons = []
        
        if analysis['rms'] > 0.1:
            quality_score += 2
            reasons.append("good_energy")
        elif analysis['rms'] > 0.05:
            quality_score += 1
            reasons.append("adequate_energy")
        else:
            reasons.append("low_energy")
        
        if analysis['voice_ratio'] > 0.6:
            quality_score += 2
            reasons.append("excellent_voice_content")
        elif analysis['voice_ratio'] > 0.4:
            quality_score += 1
            reasons.append("good_voice_content")
        else:
            reasons.append("poor_voice_content")
        
        if analysis['dynamic_range'] > 0.5:
            quality_score += 1
            reasons.append("good_variation")
        
        print(f"   🎯 Quality Score: {quality_score}/5")
        print(f"   📝 Reasons: {', '.join(reasons)}")
        
        # Play sample (brief)
        try:
            print(f"   🔊 Playing 3-second sample...")
            subprocess.run(['afplay', str(audio_path)], timeout=3)
            time.sleep(0.5)  # Brief pause between samples
        except:
            print(f"   ⚠️  Could not play audio sample")

def main():
    validate_top_samples()

if __name__ == "__main__":
    main()