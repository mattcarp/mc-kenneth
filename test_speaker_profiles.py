import io
import math
import struct
import sys
import types
import wave

import numpy as np
from fastapi.testclient import TestClient

# Isolate tests from optional maritime capture dependencies.
api_maritime_aviation_stub = types.ModuleType("api_maritime_aviation")
api_maritime_aviation_stub.add_maritime_aviation_routes = lambda app: app
sys.modules["api_maritime_aviation"] = api_maritime_aviation_stub

import api_server


client = TestClient(api_server.app)


def setup_function() -> None:
    api_server.SPEAKER_PROFILES.clear()


def _make_voice_wav(
    fundamental_hz: float, duration_sec: float = 1.4, sample_rate: int = 16000
) -> bytes:
    sample_count = int(duration_sec * sample_rate)
    t = np.arange(sample_count, dtype=np.float32) / sample_rate
    signal = (
        0.60 * np.sin(2.0 * math.pi * fundamental_hz * t)
        + 0.25 * np.sin(2.0 * math.pi * fundamental_hz * 2.0 * t)
        + 0.15 * np.sin(2.0 * math.pi * fundamental_hz * 3.0 * t)
    )
    signal = np.clip(signal, -0.99, 0.99)
    pcm16 = (signal * 32767.0).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack(f"<{len(pcm16)}h", *pcm16))
    return buf.getvalue()


def test_identify_speaker_creates_profile_with_demographics() -> None:
    audio = _make_voice_wav(138.0)
    response = client.post(
        "/voice/speakers/identify",
        files={"audio_file": ("capture_1.wav", audio, "audio/wav")},
        data={"capture_id": "cap-001", "frequency_hz": "156800000"},
    )

    assert response.status_code == 200
    payload = response.json()
    profile = payload["profile"]

    assert payload["matched_existing_profile"] is False
    assert payload["similarity"] == 1.0
    assert profile["captures_count"] == 1
    assert profile["gender_estimate"] in {"male", "female", "unknown"}
    assert isinstance(profile["age_estimate"], int)
    assert "age_range" in profile


def test_identify_speaker_matches_existing_profile_across_captures() -> None:
    first = _make_voice_wav(132.0)
    second = _make_voice_wav(134.0)

    first_resp = client.post(
        "/voice/speakers/identify",
        files={"audio_file": ("capture_a.wav", first, "audio/wav")},
        data={"capture_id": "cap-a"},
    )
    assert first_resp.status_code == 200
    speaker_id = first_resp.json()["speaker_id"]

    second_resp = client.post(
        "/voice/speakers/identify",
        files={"audio_file": ("capture_b.wav", second, "audio/wav")},
        data={"capture_id": "cap-b"},
    )
    assert second_resp.status_code == 200
    second_payload = second_resp.json()

    assert second_payload["matched_existing_profile"] is True
    assert second_payload["speaker_id"] == speaker_id
    assert second_payload["profile"]["captures_count"] == 2
    assert second_payload["profile"]["last_capture_id"] == "cap-b"


def test_identify_speaker_creates_new_profile_for_different_voice() -> None:
    low_voice = _make_voice_wav(110.0)
    high_voice = _make_voice_wav(240.0)

    first_resp = client.post(
        "/voice/speakers/identify",
        files={"audio_file": ("speaker_low.wav", low_voice, "audio/wav")},
        data={"capture_id": "cap-low"},
    )
    assert first_resp.status_code == 200
    low_speaker_id = first_resp.json()["speaker_id"]

    second_resp = client.post(
        "/voice/speakers/identify",
        files={"audio_file": ("speaker_high.wav", high_voice, "audio/wav")},
        data={"capture_id": "cap-high"},
    )
    assert second_resp.status_code == 200
    high_payload = second_resp.json()

    assert high_payload["matched_existing_profile"] is False
    assert high_payload["speaker_id"] != low_speaker_id

    list_resp = client.get("/voice/speakers")
    assert list_resp.status_code == 200
    profiles = list_resp.json()
    assert len(profiles) == 2
