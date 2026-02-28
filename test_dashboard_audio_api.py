import sys
import types
from pathlib import Path

from fastapi.testclient import TestClient

# Isolate tests from optional maritime capture dependencies.
api_maritime_aviation_stub = types.ModuleType("api_maritime_aviation")
api_maritime_aviation_stub.add_maritime_aviation_routes = lambda app: app
sys.modules["api_maritime_aviation"] = api_maritime_aviation_stub

import api_server


client = TestClient(api_server.app)


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
