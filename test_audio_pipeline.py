#!/usr/bin/env python3
"""
Test suite for ElevenLabs audio processing pipeline
Tests preprocessing, client integration, and RF processor
"""

import sys
import os
import numpy as np
import soundfile as sf
from pathlib import Path
import tempfile
import logging

# Add src to path
sys.path.insert(0, 'src')

try:
    from audio_preprocessor import AudioPreprocessor, AudioPreprocessorConfig
    from elevenlabs_client import ElevenLabsClient
    from elevenlabs_rf_processor import ElevenLabsRFProcessor
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_audio(duration=6.0, sample_rate=44100, add_noise=True):
    """Create synthetic test audio with voice-like signal + noise"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Voice-like signal (fundamental + harmonics)
    voice_freq = 200
    voice = (np.sin(2 * np.pi * voice_freq * t) * 0.3 +
             np.sin(2 * np.pi * voice_freq * 2 * t) * 0.2 +
             np.sin(2 * np.pi * voice_freq * 3 * t) * 0.1)
    
    # Add modulation
    voice *= (1 + 0.5 * np.sin(2 * np.pi * 3 * t))
    
    if add_noise:
        # RF-style noise
        rf_noise = np.random.normal(0, 0.4, len(t))
        
        # Intermittent static bursts
        for i in range(int(duration)):
            start_idx = int(i * sample_rate)
            burst_length = int(0.1 * sample_rate)
            if i % 2 == 0:
                rf_noise[start_idx:start_idx + burst_length] *= 3
        
        audio = voice + rf_noise
    else:
        audio = voice
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8
    return audio, sample_rate


def test_audio_preprocessor():
    """Test AudioPreprocessor functionality"""
    print("\n=== Testing AudioPreprocessor ===")
    
    try:
        # Create test audio
        audio_data, sr = create_test_audio()
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            sf.write(tmp.name, audio_data, sr)
            test_file = Path(tmp.name)
        
        # Test preprocessor
        preprocessor = AudioPreprocessor()
        
        # Test file processing
        result_path = preprocessor.process_file(test_file)
        
        if result_path.exists():
            # Load and verify result
            processed_data, processed_sr = sf.read(result_path)
            
            print(f"✅ File processing successful")
            print(f"   Original: {len(audio_data)} samples @ {sr}Hz")
            print(f"   Processed: {len(processed_data)} samples @ {processed_sr}Hz")
            print(f"   Target SR: {preprocessor.config.target_sample_rate}Hz")
            
            # Test streaming chunk processing
            chunk = audio_data[:sr]  # 1 second chunk
            processed_chunk = preprocessor.process_stream_chunk(chunk, sr)
            print(f"✅ Streaming chunk processing successful")
            print(f"   Chunk: {len(chunk)} → {len(processed_chunk)} samples")
            
            # Cleanup
            test_file.unlink()
            result_path.unlink()
            
            return True
            
        else:
            print("❌ Preprocessor failed - no output file")
            return False
            
    except Exception as e:
        print(f"❌ Preprocessor test failed: {e}")
        return False


def test_elevenlabs_client():
    """Test ElevenLabsClient (mock test without API call)"""
    print("\n=== Testing ElevenLabsClient ===")
    
    try:
        # Check if API key is available
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("⚠️  No ELEVENLABS_API_KEY found - testing client initialization only")
            try:
                # This should fail gracefully
                client = ElevenLabsClient()
                print("❌ Should have failed without API key")
                return False
            except ValueError as e:
                print(f"✅ Correctly rejected missing API key: {e}")
                return True
        else:
            # Test with API key present
            client = ElevenLabsClient(api_key)
            print(f"✅ Client initialized with API key")
            print(f"   Config: timeout={client.config.timeout_s}s, retries={client.config.max_retries}")
            
            # Test file validation
            fake_file = Path("nonexistent.wav")
            try:
                client.isolate_file(fake_file)
                print("❌ Should have failed with nonexistent file")
                return False
            except FileNotFoundError:
                print("✅ Correctly rejected nonexistent file")
                return True
            
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        return False


def test_rf_processor():
    """Test ElevenLabsRFProcessor (without API calls)"""
    print("\n=== Testing ElevenLabsRFProcessor ===")
    
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("⚠️  No ELEVENLABS_API_KEY found - testing initialization only")
            try:
                processor = ElevenLabsRFProcessor()
                print("❌ Should have failed without API key")
                return False
            except ValueError as e:
                print(f"✅ Correctly rejected missing API key: {e}")
                return True
        else:
            # Test initialization with key
            processor = ElevenLabsRFProcessor(api_key)
            print("✅ RF Processor initialized")
            print(f"   Has preprocessor: {processor.preprocessor is not None}")
            print(f"   Has ElevenLabs client: {processor.client is not None}")
            
            # Test streaming audio processing (preprocessing only)
            audio_data, sr = create_test_audio(duration=2.0)
            
            print("✅ Created test audio for streaming test")
            print(f"   Duration: {len(audio_data)/sr:.1f}s @ {sr}Hz")
            
            # Note: Not calling process_streaming_audio as it would hit the API
            print("⚠️  Skipping API call test - would require live API")
            
            return True
            
    except Exception as e:
        print(f"❌ RF Processor test failed: {e}")
        return False


def test_pipeline_integration():
    """Test end-to-end pipeline (preprocessing only, no API calls)"""
    print("\n=== Testing Pipeline Integration ===")
    
    try:
        # Create test audio file
        audio_data, sr = create_test_audio()
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            sf.write(tmp.name, audio_data, sr)
            test_file = Path(tmp.name)
        
        # Test preprocessing stage only
        preprocessor = AudioPreprocessor()
        processed_file = preprocessor.process_file(test_file)
        
        if processed_file.exists():
            # Verify processed file
            processed_data, processed_sr = sf.read(processed_file)
            
            print("✅ Pipeline preprocessing stage successful")
            print(f"   Original: {len(audio_data)} samples @ {sr}Hz")
            print(f"   Processed: {len(processed_data)} samples @ {processed_sr}Hz")
            print(f"   Format: {processed_data.dtype}")
            
            # Verify it meets ElevenLabs requirements
            duration = len(processed_data) / processed_sr
            print(f"   Duration: {duration:.2f}s (min 5s required: {'✅' if duration >= 5.0 else '❌'})")
            print(f"   Sample rate: {processed_sr}Hz ({'✅' if processed_sr in [16000, 44100] else '❌'})")
            print(f"   Channels: {'mono' if processed_data.ndim == 1 else f'{processed_data.shape[1]}ch'}")
            
            # Cleanup
            test_file.unlink()
            processed_file.unlink()
            
            return duration >= 5.0 and processed_sr in [16000, 44100]
        else:
            print("❌ Pipeline preprocessing failed")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline integration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 ElevenLabs Audio Pipeline Test Suite")
    print("=" * 50)
    
    tests = [
        ("AudioPreprocessor", test_audio_preprocessor),
        ("ElevenLabsClient", test_elevenlabs_client),
        ("ElevenLabsRFProcessor", test_rf_processor),
        ("Pipeline Integration", test_pipeline_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Pipeline ready for next phase.")
        return True
    else:
        print("⚠️  Some tests failed. Review before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)