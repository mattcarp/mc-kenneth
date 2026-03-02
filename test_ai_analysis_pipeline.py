import wave
from pathlib import Path

import numpy as np

import ai_analysis_pipeline


def _write_wav(path: Path, data: np.ndarray, sample_rate: int = 16000) -> None:
    clipped = np.clip(data, -1.0, 1.0)
    pcm = (clipped * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())


def _low_stress_signal(duration_sec: float = 2.0, sample_rate: int = 16000) -> np.ndarray:
    t = np.linspace(0, duration_sec, int(duration_sec * sample_rate), endpoint=False)
    return 0.08 * np.sin(2.0 * np.pi * 180.0 * t)


def _high_stress_signal(duration_sec: float = 2.0, sample_rate: int = 16000) -> np.ndarray:
    t = np.linspace(0, duration_sec, int(duration_sec * sample_rate), endpoint=False)
    carrier = np.sin(2.0 * np.pi * (180.0 + 90.0 * np.sin(2.0 * np.pi * 7.0 * t)) * t)
    envelope = np.where(np.sin(2.0 * np.pi * 4.0 * t) > 0, 0.9, 0.1)
    return 0.45 * carrier * envelope + np.random.default_rng(7).normal(0.0, 0.02, len(t))


def test_compute_stress_score_is_bounded_and_sensitive(tmp_path: Path) -> None:
    low_path = tmp_path / "low.wav"
    high_path = tmp_path / "high.wav"
    _write_wav(low_path, _low_stress_signal())
    _write_wav(high_path, _high_stress_signal())

    low_score = ai_analysis_pipeline.compute_stress_score(low_path)
    high_score = ai_analysis_pipeline.compute_stress_score(high_path)

    assert 0 <= low_score <= 100
    assert 0 <= high_score <= 100
    assert high_score > low_score


def test_extract_stress_features_non_negative(tmp_path: Path) -> None:
    path = tmp_path / "sample.wav"
    _write_wav(path, _high_stress_signal())

    features = ai_analysis_pipeline.extract_stress_features(path)

    assert features.pitch_variance_hz2 >= 0
    assert features.speech_rate_per_sec >= 0
    assert features.rms_energy >= 0
    assert 0 <= features.voiced_ratio <= 1


def test_classify_threat_keywords_detects_matches() -> None:
    result = ai_analysis_pipeline.classify_threat_keywords(
        "Mayday mayday, we need help immediately. Possible fire in engine room."
    )

    assert result["is_flagged"] is True
    assert "mayday" in result["matched_terms"]
    assert "help" in result["matched_terms"]
    assert "fire" in result["matched_terms"]


def test_analyze_audio_file_combines_transcription_stress_and_keywords(
    monkeypatch, tmp_path: Path
) -> None:
    path = tmp_path / "analysis.wav"
    _write_wav(path, _high_stress_signal())

    monkeypatch.setattr(
        ai_analysis_pipeline,
        "transcribe_audio_file",
        lambda p, config: {
            "text": "Distress call. We need immediate help.",
            "language": "en",
            "segments": [{"start": 0.0, "end": 1.0, "text": "Distress call."}],
        },
    )

    result = ai_analysis_pipeline.analyze_audio_file(path)

    assert result["audio_file"].endswith("analysis.wav")
    assert 0 <= result["stress_score"] <= 100
    assert result["threat_classification"]["is_flagged"] is True
    assert "distress" in result["threat_classification"]["matched_terms"]


def test_analyze_audio_file_triggers_telegram_for_high_stress(
    monkeypatch, tmp_path: Path
) -> None:
    path = tmp_path / "analysis.wav"
    _write_wav(path, _high_stress_signal())
    sent = []

    monkeypatch.setattr(
        ai_analysis_pipeline,
        "transcribe_audio_file",
        lambda p, config: {"text": "Panic voice sample", "language": "en"},
    )
    monkeypatch.setattr(
        ai_analysis_pipeline,
        "send_telegram_alert",
        lambda message, stress_score, transcription_preview: sent.append(
            {
                "message": message,
                "stress_score": stress_score,
                "transcription_preview": transcription_preview,
            }
        )
        or True,
    )

    result = ai_analysis_pipeline.analyze_audio_file(path)

    assert result["stress_score"] > ai_analysis_pipeline.HIGH_STRESS_THRESHOLD
    assert len(sent) == 1
    assert sent[0]["stress_score"] == result["stress_score"]


def test_find_audio_files_filters_known_extensions(tmp_path: Path) -> None:
    (tmp_path / "a.wav").write_bytes(b"")
    (tmp_path / "b.mp3").write_bytes(b"")
    (tmp_path / "c.txt").write_text("ignore", encoding="utf-8")

    files = ai_analysis_pipeline.find_audio_files(tmp_path)

    assert [file.name for file in files] == ["a.wav", "b.mp3"]
