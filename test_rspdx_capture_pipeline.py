from __future__ import annotations

import argparse
import json
from pathlib import Path

import rspdx_capture_pipeline as pipeline


def _args(tmp_path: Path, **overrides):
    base = {
        "config": None,
        "output_dir": str(tmp_path),
        "frequency_hz": None,
        "frequency_mhz": None,
        "sample_rate": None,
        "gain": None,
        "duration": None,
        "interval": None,
        "max_captures": None,
        "device_arg": None,
        "validate": True,
        "verbose": False,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_validate_capture_thresholds() -> None:
    passed = pipeline.validate_capture({"samples_captured": 1024, "average_power_dbfs": -75, "nonzero_ratio": 0.2})
    failed = pipeline.validate_capture({"samples_captured": 1024, "average_power_dbfs": -119, "nonzero_ratio": 0.0001})

    assert passed["passed"] is True
    assert "non-zero" in passed["notes"]
    assert failed["passed"] is False


def test_capture_log_round_trip(tmp_path: Path) -> None:
    entries = [
        {"id": "a", "created_at": "2026-03-05T00:00:00Z", "average_power_dbfs": -70.0},
        {"id": "b", "created_at": "2026-03-05T00:01:00Z", "average_power_dbfs": -71.0},
    ]

    for entry in entries:
        pipeline.append_capture_log(tmp_path, entry)

    recent = pipeline.load_recent_captures(tmp_path, limit=50)
    assert [item["id"] for item in recent] == ["a", "b"]

    pipeline.write_recent_captures(tmp_path, recent)
    summary = json.loads((tmp_path / "captures_recent.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in summary] == ["a", "b"]


def test_run_pipeline_validate_writes_status_validation_and_closes_stream(monkeypatch, tmp_path: Path) -> None:
    events = {"deactivate": 0, "close": 0}

    class FakeSdr:
        def deactivateStream(self, _stream):
            events["deactivate"] += 1

        def closeStream(self, _stream):
            events["close"] += 1

    fake_sdr = FakeSdr()

    monkeypatch.setattr(pipeline, "open_device", lambda config, logger: fake_sdr)
    monkeypatch.setattr(pipeline, "setup_device", lambda sdr, config, logger: None)
    monkeypatch.setattr(pipeline, "setup_stream", lambda sdr, config, logger: "rx")
    monkeypatch.setattr(
        pipeline,
        "capture_once",
        lambda *args, **kwargs: {
            "id": "rspdx_capture_1",
            "created_at": "2026-03-05T00:00:00Z",
            "frequency_hz": 156800000,
            "frequency_mhz": 156.8,
            "duration_sec": 1.0,
            "samples_captured": 2000000,
            "sample_format": "CF32",
            "file": "rspdx_capture_1.cf32",
            "average_power_dbfs": -60.0,
            "max_magnitude": 0.91,
            "nonzero_ratio": 0.11,
            "elapsed_sec": 1.0,
        },
    )

    rc = pipeline.run_pipeline(_args(tmp_path, validate=True))

    assert rc == 0

    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert status["captures_count"] == 1
    assert status["validation"]["passed"] is True
    assert status["state"] == "stopped"

    validation = json.loads((tmp_path / "validation.json").read_text(encoding="utf-8"))
    assert validation["passed"] is True
    assert validation["capture_id"] == "rspdx_capture_1"

    assert events["deactivate"] == 1
    assert events["close"] == 1


def test_run_pipeline_open_device_failure_records_error_state(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pipeline, "open_device", lambda config, logger: (_ for _ in ()).throw(RuntimeError("device missing")))

    rc = pipeline.run_pipeline(_args(tmp_path, validate=False))

    assert rc == 2
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert status["errors"] == 1
    assert "device missing" in status["last_error"]
    assert status["state"] == "error"
