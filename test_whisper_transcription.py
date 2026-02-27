import sys
import types
import wave
from pathlib import Path

import numpy as np

# Keep tests isolated from optional audio runtime dependencies.
if "soundfile" not in sys.modules:
    soundfile_stub = types.ModuleType("soundfile")
    soundfile_stub.write = lambda *args, **kwargs: None
    sys.modules["soundfile"] = soundfile_stub

if "scipy" not in sys.modules:
    scipy_stub = types.ModuleType("scipy")
    scipy_stub.signal = types.SimpleNamespace()
    sys.modules["scipy"] = scipy_stub

import autonomous_voice_hunter
from whisper_transcription import WhisperConfig, transcribe_audio_file


def _write_test_wav(path: Path, sample_rate: int = 16000, duration_sec: float = 0.2) -> None:
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    signal = (0.3 * np.sin(2.0 * np.pi * 440.0 * t) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(signal.tobytes())


def test_transcribe_audio_file_uses_faster_whisper(monkeypatch, tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.wav"
    _write_test_wav(audio_path)

    class DummySegment:
        def __init__(self, start: float, end: float, text: str) -> None:
            self.start = start
            self.end = end
            self.text = text

    class DummyInfo:
        language = "en"
        language_probability = 0.99
        duration = 1.2

    class DummyModel:
        def __init__(self, model_size: str, device: str, compute_type: str) -> None:
            assert model_size == "large-v3"
            assert device == "auto"
            assert compute_type == "default"

        def transcribe(self, audio_file: str, beam_size: int, vad_filter: bool, language=None):
            assert audio_file.endswith("sample.wav")
            assert beam_size == 5
            assert vad_filter is True
            assert language is None
            return iter(
                [
                    DummySegment(0.0, 0.5, " hello "),
                    DummySegment(0.5, 1.0, "world"),
                ]
            ), DummyInfo()

    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        types.SimpleNamespace(WhisperModel=DummyModel),
    )

    result = transcribe_audio_file(audio_path, WhisperConfig())

    assert result["text"] == "hello world"
    assert result["language"] == "en"
    assert len(result["segments"]) == 2
    assert result["segments"][0]["text"] == "hello"


def test_autonomous_hunter_auto_transcribe_writes_artifacts(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    hunter = autonomous_voice_hunter.AutonomousVoiceHunter(session_name="test-session")

    audio_path = hunter.session_dir / "capture.wav"
    _write_test_wav(audio_path)

    def fake_transcribe(path, config):
        assert str(path).endswith("capture.wav")
        assert config.model_size == "large-v3"
        return {
            "text": "distress call from vessel",
            "segments": [{"start": 0.0, "end": 1.0, "text": "distress call from vessel"}],
            "language": "en",
        }

    monkeypatch.setattr(autonomous_voice_hunter, "transcribe_audio_file", fake_transcribe)

    result = hunter._auto_transcribe_capture(audio_path, "CH16", 156_800_000.0)

    assert result["text"] == "distress call from vessel"
    assert len(hunter.transcriptions) == 1
    assert (hunter.transcripts_dir / "capture.txt").exists()
    assert (hunter.transcripts_dir / "capture.json").exists()
