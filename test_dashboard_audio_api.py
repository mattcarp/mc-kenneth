import sys
import types
import wave
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

# Isolate tests from optional maritime capture dependencies.
api_maritime_aviation_stub = types.ModuleType("api_maritime_aviation")
api_maritime_aviation_stub.add_maritime_aviation_routes = lambda app: app
sys.modules["api_maritime_aviation"] = api_maritime_aviation_stub

import api_server


client = TestClient(api_server.app)


def _write_test_wav(path: Path, sample_rate: int = 16000, duration_sec: float = 0.3) -> None:
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    signal = (0.2 * np.sin(2.0 * np.pi * 440.0 * t) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(signal.tobytes())


def test_audio_api_serves_wav_clip(tmp_path: Path, monkeypatch) -> None:
    wav_path = tmp_path / "sample.wav"
    wav_path.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")

    monkeypatch.setattr(api_server, "AUDIO_SEARCH_DIRS", [tmp_path])

    response = client.get("/api/audio/sample.wav")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")
    assert response.content.startswith(b"RIFF")


def test_audio_api_rejects_unknown_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(api_server, "AUDIO_SEARCH_DIRS", [tmp_path])

    response = client.get("/api/audio/missing.wav")

    assert response.status_code == 404


def test_transcribe_endpoint_returns_text(tmp_path: Path, monkeypatch) -> None:
    wav_path = tmp_path / "sample.wav"
    _write_test_wav(wav_path)
    monkeypatch.setattr(api_server, "AUDIO_SEARCH_DIRS", [tmp_path])

    def fake_transcribe(path, config):
        assert path == wav_path
        assert config.model_size == "tiny"
        assert config.backend == "auto"
        assert config.language == "en"
        return {
            "text": "distress call",
            "language": "en",
            "segments": [{"start": 0.0, "end": 0.8, "text": "distress call"}],
            "backend": "faster-whisper",
            "model": "tiny",
        }

    monkeypatch.setattr(api_server, "transcribe_audio_file", fake_transcribe)

    response = client.get(
        "/transcribe",
        params={"file": "sample.wav", "model_size": "tiny", "backend": "auto", "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["file"] == "sample.wav"
    assert body["text"] == "distress call"
    assert body["language"] == "en"
    assert body["backend"] == "faster-whisper"
    assert body["model"] == "tiny"
    assert body["segments"][0]["text"] == "distress call"


def test_transcribe_endpoint_returns_bad_request_for_invalid_backend(
    tmp_path: Path, monkeypatch
) -> None:
    wav_path = tmp_path / "sample.wav"
    _write_test_wav(wav_path)
    monkeypatch.setattr(api_server, "AUDIO_SEARCH_DIRS", [tmp_path])

    def fake_transcribe(path, config):
        raise ValueError(
            "Unsupported whisper backend 'broken'. Use one of: auto, faster-whisper, openai-whisper"
        )

    monkeypatch.setattr(api_server, "transcribe_audio_file", fake_transcribe)

    response = client.get(
        "/transcribe",
        params={"file": "sample.wav", "backend": "broken"},
    )

    assert response.status_code == 400
    assert "Unsupported whisper backend 'broken'" in response.json()["detail"]


def test_stress_endpoint_returns_score_and_features(tmp_path: Path, monkeypatch) -> None:
    wav_path = tmp_path / "sample.wav"
    _write_test_wav(wav_path)
    monkeypatch.setattr(api_server, "AUDIO_SEARCH_DIRS", [tmp_path])
    monkeypatch.setattr(
        api_server,
        "extract_stress_features",
        lambda path: types.SimpleNamespace(
            pitch_variance_hz2=320.0,
            speech_rate_per_sec=0.8,
            rms_energy=0.12,
            voiced_ratio=0.7,
        ),
    )
    monkeypatch.setattr(api_server, "score_stress", lambda features: 42)

    response = client.get("/stress", params={"file": "sample.wav"})

    assert response.status_code == 200
    body = response.json()
    assert body["file"] == "sample.wav"
    assert body["stress_score"] == 42
    assert body["features"]["pitch_variance_hz2"] == 320.0


def test_analysis_audio_endpoint_returns_pipeline_payload(tmp_path: Path, monkeypatch) -> None:
    wav_path = tmp_path / "sample.wav"
    _write_test_wav(wav_path)
    monkeypatch.setattr(api_server, "AUDIO_SEARCH_DIRS", [tmp_path])

    def fake_analyze(path, whisper_config=None, flagged_terms=None):
        assert path == wav_path
        assert whisper_config.model_size == "tiny"
        assert whisper_config.backend == "auto"
        assert whisper_config.language == "en"
        return {
            "audio_file": str(path),
            "transcript": {"text": "mayday we need help", "language": "en", "segments": []},
            "stress_score": 91,
            "stress_features": {
                "pitch_variance_hz2": 742.0,
                "speech_rate_per_sec": 1.2,
                "rms_energy": 0.31,
                "voiced_ratio": 0.76,
            },
            "threat_classification": {
                "is_flagged": True,
                "matched_terms": ["help", "mayday"],
                "match_count": 2,
            },
        }

    monkeypatch.setattr(api_server, "analyze_audio_file", fake_analyze)

    response = client.get(
        "/analysis/audio",
        params={"file": "sample.wav", "model_size": "tiny", "backend": "auto", "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["audio_file"].endswith("sample.wav")
    assert body["transcript"]["text"] == "mayday we need help"
    assert body["stress_score"] == 91
    assert body["threat_classification"]["is_flagged"] is True


def test_analysis_audio_endpoint_returns_bad_request_for_invalid_backend(
    tmp_path: Path, monkeypatch
) -> None:
    wav_path = tmp_path / "sample.wav"
    _write_test_wav(wav_path)
    monkeypatch.setattr(api_server, "AUDIO_SEARCH_DIRS", [tmp_path])

    def fake_analyze(path, whisper_config=None, flagged_terms=None):
        raise ValueError(
            "Unsupported whisper backend 'broken'. Use one of: auto, faster-whisper, openai-whisper"
        )

    monkeypatch.setattr(api_server, "analyze_audio_file", fake_analyze)

    response = client.get(
        "/analysis/audio",
        params={"file": "sample.wav", "backend": "broken"},
    )

    assert response.status_code == 400
    assert "Unsupported whisper backend 'broken'" in response.json()["detail"]
