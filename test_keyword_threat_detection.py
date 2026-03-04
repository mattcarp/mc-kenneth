from pathlib import Path

import pytest

import ai_analysis_pipeline
import keyword_threat_detection


def _transcription(text: str, language: str = "en") -> dict:
    return {
        "text": text,
        "language": language,
        "segments": [{"start": 0.0, "end": 1.0, "text": text}],
    }


@pytest.fixture(autouse=True)
def _alerts_file_isolation(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(keyword_threat_detection, "ALERTS_FILE", tmp_path / "alerts.json")


def test_mayday_detected_scores_high() -> None:
    result = keyword_threat_detection.detect_threats(
        _transcription("MAYDAY MAYDAY engine failure")
    )

    assert result["keyword"] == "mayday"
    assert result["threat_score"] >= 80
    assert result["alert"] is True


def test_pan_pan_detected_scores_elevated() -> None:
    result = keyword_threat_detection.detect_threats(_transcription("PAN-PAN request support"))

    assert result["keyword"] in {"pan-pan", "pan pan"}
    assert result["threat_score"] >= 60


def test_sos_detected_scores_high() -> None:
    result = keyword_threat_detection.detect_threats(_transcription("SOS immediate help"))

    assert result["keyword"] == "sos"
    assert result["threat_score"] >= 70


def test_italian_keyword_soccorso_detected() -> None:
    result = keyword_threat_detection.detect_threats(
        _transcription("Abbiamo bisogno di SOCCORSO subito", language="it")
    )

    assert result["keyword"] == "soccorso"
    assert result["alert"] is True


def test_maltese_keyword_ajjut_detected() -> None:
    result = keyword_threat_detection.detect_threats(
        _transcription("Ghandna bzonn AJJUT issa", language="mt")
    )

    assert result["keyword"] == "ajjut"
    assert result["alert"] is True


def test_arabic_keyword_najda_detected() -> None:
    result = keyword_threat_detection.detect_threats(_transcription("نحتاج نجدة فورا", language="ar"))

    assert result["keyword"] == "نجدة"
    assert result["alert"] is True


def test_no_keywords_scores_zero() -> None:
    result = keyword_threat_detection.detect_threats(
        _transcription("Routine transmission all systems nominal")
    )

    assert result["keyword"] is None
    assert result["threat_score"] == 0
    assert result["alert"] is False


def test_criminal_coordination_phrases_score_moderate() -> None:
    result = keyword_threat_detection.detect_threats(
        _transcription("Meet at dock 3 then drop the shipment")
    )

    assert result["keyword"] in {"meet at", "drop the", "shipment"}
    assert result["threat_score"] >= 40


def test_output_includes_required_fields() -> None:
    result = keyword_threat_detection.detect_threats(
        _transcription("MAYDAY", language="en"),
        frequency_hz=156.8,
    )

    assert set(result.keys()) == {
        "keyword",
        "threat_score",
        "language",
        "alert",
        "timestamp",
        "frequency_hz",
    }
    assert result["language"] == "en"
    assert result["frequency_hz"] == 156.8
    assert isinstance(result["timestamp"], str)


def test_analyse_transmission_integrates_keyword_detector(monkeypatch, tmp_path: Path) -> None:
    alerts_path = tmp_path / "alerts.json"
    monkeypatch.setattr(keyword_threat_detection, "ALERTS_FILE", alerts_path)

    transcription = _transcription("MAYDAY this is vessel alpha", language="en")
    result = ai_analysis_pipeline.analyse_transmission(transcription, frequency_hz=121500000.0)

    assert result["alert"] is True
    assert result["keyword"] == "mayday"
    assert result["threat_score"] >= 80
    assert result["frequency_hz"] == 121500000.0
    assert alerts_path.exists() is True
