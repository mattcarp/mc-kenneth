#!/usr/bin/env python3
"""
RSPdx-R2 SDR capture pipeline.

Captures raw IQ samples via SoapySDR (sdrplay driver), logs capture metadata,
updates a status JSON, and supports a validation mode for quick sanity checks.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

try:
    import SoapySDR  # type: ignore
except Exception as exc:  # pragma: no cover - environment dependent
    SoapySDR = None
    SOAPY_IMPORT_ERROR = exc
else:
    SOAPY_IMPORT_ERROR = None


DEFAULT_CONFIG_PATH = Path("config/rspdx_capture_pipeline.json")
DEFAULT_OUTPUT_DIR = Path("rf_captures/rspdx_pipeline")


@dataclass
class CaptureConfig:
    frequency_hz: int
    sample_rate: int
    gain: float
    duration_sec: float
    bandwidth: Optional[int]
    device_args: Dict[str, Any]
    channel: int
    sample_format: str
    stream_timeout_sec: float
    buffer_len: int
    capture_interval_sec: float
    max_captures: int


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def isoformat(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def merge_config(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def build_capture_config(config: Dict[str, Any], args: argparse.Namespace) -> CaptureConfig:
    frequency_hz = int(args.frequency_hz or config.get("frequency_hz", 156_800_000))
    if args.frequency_mhz is not None:
        frequency_hz = int(float(args.frequency_mhz) * 1e6)

    return CaptureConfig(
        frequency_hz=frequency_hz,
        sample_rate=int(args.sample_rate or config.get("sample_rate", 2_000_000)),
        gain=float(args.gain if args.gain is not None else config.get("gain", 40.0)),
        duration_sec=float(args.duration if args.duration is not None else config.get("duration_sec", 10.0)),
        bandwidth=int(config.get("bandwidth")) if config.get("bandwidth") is not None else None,
        device_args=dict(config.get("device_args", {"driver": "sdrplay"})),
        channel=int(config.get("channel", 0)),
        sample_format=str(config.get("sample_format", "CF32")),
        stream_timeout_sec=float(config.get("stream_timeout_sec", 0.5)),
        buffer_len=int(config.get("buffer_len", 16384)),
        capture_interval_sec=float(args.interval if args.interval is not None else config.get("capture_interval_sec", 1.0)),
        max_captures=int(args.max_captures if args.max_captures is not None else config.get("max_captures", 0)),
    )


def configure_logging(output_dir: Path, verbose: bool) -> logging.Logger:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "pipeline.log"
    logger = logging.getLogger("rspdx_pipeline")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def open_device(config: CaptureConfig, logger: logging.Logger):
    if SoapySDR is None:
        raise RuntimeError(f"SoapySDR not available: {SOAPY_IMPORT_ERROR}")

    logger.info("Opening SDR device with args: %s", config.device_args)
    return SoapySDR.Device(config.device_args)


def setup_device(sdr, config: CaptureConfig, logger: logging.Logger) -> None:
    logger.info(
        "Configuring SDR: freq=%.3f MHz | rate=%.3f MSPS | gain=%.1f",
        config.frequency_hz / 1e6,
        config.sample_rate / 1e6,
        config.gain,
    )
    sdr.setSampleRate(SoapySDR.SOAPY_SDR_RX, config.channel, config.sample_rate)
    sdr.setFrequency(SoapySDR.SOAPY_SDR_RX, config.channel, config.frequency_hz)
    sdr.setGain(SoapySDR.SOAPY_SDR_RX, config.channel, config.gain)
    if config.bandwidth:
        sdr.setBandwidth(SoapySDR.SOAPY_SDR_RX, config.channel, config.bandwidth)


def setup_stream(sdr, config: CaptureConfig, logger: logging.Logger):
    fmt = config.sample_format.upper()
    if fmt != "CF32":
        raise ValueError("Only CF32 sample format is supported in this pipeline.")
    logger.info("Setting up stream (format=%s)", fmt)
    rx_stream = sdr.setupStream(SoapySDR.SOAPY_SDR_RX, SoapySDR.SOAPY_SDR_CF32)
    sdr.activateStream(rx_stream)
    return rx_stream


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def compute_dbfs(power: float) -> float:
    if power <= 0:
        return -120.0
    return 10.0 * math.log10(power)


def capture_once(
    sdr,
    rx_stream,
    config: CaptureConfig,
    output_dir: Path,
    logger: logging.Logger,
    capture_index: int,
) -> Dict[str, Any]:
    timestamp = utc_now()
    stamp = timestamp.strftime("%Y%m%d_%H%M%S")
    base_name = f"rspdx_capture_{stamp}_{capture_index:04d}"
    iq_path = output_dir / f"{base_name}.cf32"
    meta_path = output_dir / f"{base_name}.json"

    samples_needed = int(config.sample_rate * config.duration_sec)
    buffer_len = config.buffer_len
    timeout_us = int(config.stream_timeout_sec * 1e6)

    logger.info("Capture %s -> %s samples", base_name, samples_needed)

    total_samples = 0
    power_acc = 0.0
    max_mag = 0.0
    nonzero_samples = 0
    start_time = time.time()

    with iq_path.open("wb") as iq_file:
        while total_samples < samples_needed:
            to_read = min(buffer_len, samples_needed - total_samples)
            buff = np.zeros(to_read, dtype=np.complex64)
            sr = sdr.readStream(rx_stream, [buff], to_read, timeoutUs=timeout_us)
            if sr.ret > 0:
                valid = buff[: sr.ret]
                iq_file.write(valid.tobytes())
                mags = np.abs(valid)
                power_acc += float(np.vdot(valid, valid).real)
                max_mag = max(max_mag, float(mags.max(initial=0.0)))
                nonzero_samples += int(np.count_nonzero(mags))
                total_samples += sr.ret
                continue
            if sr.ret == SoapySDR.SOAPY_SDR_TIMEOUT:
                logger.debug("Read timeout after %s samples", total_samples)
                continue
            logger.warning("Read error (%s) after %s samples", sr.ret, total_samples)
            time.sleep(0.05)

    elapsed = time.time() - start_time
    avg_power = safe_div(power_acc, total_samples)
    avg_power_dbfs = compute_dbfs(avg_power)
    nonzero_ratio = safe_div(nonzero_samples, total_samples)

    metadata = {
        "id": base_name,
        "created_at": isoformat(timestamp),
        "frequency_hz": config.frequency_hz,
        "frequency_mhz": round(config.frequency_hz / 1e6, 6),
        "sample_rate": config.sample_rate,
        "duration_sec": config.duration_sec,
        "samples_captured": total_samples,
        "sample_format": config.sample_format,
        "file": iq_path.name,
        "average_power_dbfs": round(avg_power_dbfs, 3),
        "max_magnitude": round(max_mag, 6),
        "nonzero_ratio": round(nonzero_ratio, 6),
        "elapsed_sec": round(elapsed, 3),
    }

    with meta_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    return metadata


def append_capture_log(output_dir: Path, metadata: Dict[str, Any]) -> None:
    log_path = output_dir / "captures.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(metadata) + "\n")


def update_status(output_dir: Path, status: Dict[str, Any]) -> None:
    status_path = output_dir / "status.json"
    with status_path.open("w", encoding="utf-8") as handle:
        json.dump(status, handle, indent=2)


def write_validation(output_dir: Path, validation: Dict[str, Any]) -> None:
    validation_path = output_dir / "validation.json"
    with validation_path.open("w", encoding="utf-8") as handle:
        json.dump(validation, handle, indent=2)


def load_recent_captures(output_dir: Path, limit: int = 50) -> List[Dict[str, Any]]:
    log_path = output_dir / "captures.jsonl"
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    captures = []
    for line in lines[-limit:]:
        try:
            captures.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return captures


def write_recent_captures(output_dir: Path, captures: List[Dict[str, Any]]) -> None:
    summary_path = output_dir / "captures_recent.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(captures, handle, indent=2)


def validate_capture(metadata: Dict[str, Any]) -> Dict[str, Any]:
    validation = {
        "timestamp": isoformat(utc_now()),
        "samples_captured": metadata.get("samples_captured", 0),
        "average_power_dbfs": metadata.get("average_power_dbfs"),
        "nonzero_ratio": metadata.get("nonzero_ratio"),
    }

    nonzero_ratio = float(metadata.get("nonzero_ratio", 0.0))
    avg_power_dbfs = float(metadata.get("average_power_dbfs", -120.0))
    passes = nonzero_ratio > 0.0005 and avg_power_dbfs > -110.0

    validation["passed"] = passes
    validation["notes"] = (
        "Samples look non-zero and powered." if passes else "Samples appear too quiet or zeroed."
    )
    return validation


def run_pipeline(args: argparse.Namespace) -> int:
    config_data = load_config(Path(args.config) if args.config else DEFAULT_CONFIG_PATH)
    overrides = {}
    if args.device_arg:
        for item in args.device_arg:
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            overrides.setdefault("device_args", {})[key] = value
    config_data = merge_config(config_data, overrides)
    config = build_capture_config(config_data, args)

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    logger = configure_logging(output_dir, args.verbose)

    status: Dict[str, Any] = {
        "pipeline": "rspdx_capture_pipeline",
        "state": "starting",
        "started_at": isoformat(utc_now()),
        "frequency_hz": config.frequency_hz,
        "sample_rate": config.sample_rate,
        "gain": config.gain,
        "duration_sec": config.duration_sec,
        "captures": [],
        "captures_count": 0,
        "errors": 0,
    }

    update_status(output_dir, status)

    try:
        sdr = open_device(config, logger)
        status["device"] = "sdrplay"
    except Exception as exc:
        logger.error("Failed to open SDR device: %s", exc)
        status["errors"] += 1
        status["state"] = "error"
        status["stopped_at"] = isoformat(utc_now())
        status["updated_at"] = status["stopped_at"]
        status["last_error"] = str(exc)
        update_status(output_dir, status)
        return 2

    rx_stream = None
    try:
        setup_device(sdr, config, logger)
        rx_stream = setup_stream(sdr, config, logger)
        status["state"] = "running"
        status["updated_at"] = isoformat(utc_now())
        update_status(output_dir, status)

        stop_requested = False

        def handle_stop(signum, frame):
            nonlocal stop_requested
            logger.info("Received signal %s, stopping after current capture", signum)
            stop_requested = True

        signal.signal(signal.SIGINT, handle_stop)
        signal.signal(signal.SIGTERM, handle_stop)

        capture_index = 1
        max_captures = config.max_captures

        while True:
            try:
                metadata = capture_once(sdr, rx_stream, config, output_dir, logger, capture_index)
                append_capture_log(output_dir, metadata)
                captures = load_recent_captures(output_dir)
                write_recent_captures(output_dir, captures)

                status["last_capture"] = metadata
                status["captures_count"] = status.get("captures_count", 0) + 1
                status["updated_at"] = isoformat(utc_now())
                update_status(output_dir, status)

                logger.info(
                    "Capture %s complete | avg power %.2f dBFS | nonzero %.3f",
                    metadata["id"],
                    metadata["average_power_dbfs"],
                    metadata["nonzero_ratio"],
                )

                if args.validate:
                    validation = validate_capture(metadata)
                    validation["capture_id"] = metadata.get("id")
                    status["validation"] = validation
                    write_validation(output_dir, validation)
                    status["updated_at"] = isoformat(utc_now())
                    update_status(output_dir, status)
                    if validation["passed"]:
                        logger.info("Validation PASSED: %s", validation["notes"])
                        status["state"] = "stopped"
                        status["stopped_at"] = isoformat(utc_now())
                        status["updated_at"] = status["stopped_at"]
                        update_status(output_dir, status)
                        return 0
                    logger.warning("Validation FAILED: %s", validation["notes"])
                    status["state"] = "error"
                    status["stopped_at"] = isoformat(utc_now())
                    status["updated_at"] = status["stopped_at"]
                    update_status(output_dir, status)
                    return 1

            except Exception as exc:
                status["errors"] = status.get("errors", 0) + 1
                status["last_error"] = str(exc)
                status["updated_at"] = isoformat(utc_now())
                update_status(output_dir, status)
                logger.exception("Capture failed: %s", exc)
                if args.validate:
                    status["state"] = "error"
                    status["stopped_at"] = isoformat(utc_now())
                    status["updated_at"] = status["stopped_at"]
                    update_status(output_dir, status)
                    return 1

            if stop_requested:
                break

            capture_index += 1
            if max_captures and capture_index > max_captures:
                break

            if config.capture_interval_sec > 0:
                time.sleep(config.capture_interval_sec)

        status["state"] = "stopped"
        status["stopped_at"] = isoformat(utc_now())
        status["updated_at"] = status["stopped_at"]
        update_status(output_dir, status)
        logger.info("Pipeline stopped. Captures saved: %s", status.get("captures_count"))
        return 0
    finally:
        if rx_stream is not None:
            try:
                sdr.deactivateStream(rx_stream)
            except Exception as exc:
                logger.warning("Failed to deactivate stream cleanly: %s", exc)
            try:
                sdr.closeStream(rx_stream)
            except Exception as exc:
                logger.warning("Failed to close stream cleanly: %s", exc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RSPdx-R2 capture pipeline")
    parser.add_argument("--config", help="Path to JSON config", default=None)
    parser.add_argument("--output-dir", help="Output directory", default=None)
    parser.add_argument("--frequency-hz", type=int, default=None)
    parser.add_argument("--frequency-mhz", type=float, default=None)
    parser.add_argument("--sample-rate", type=int, default=None)
    parser.add_argument("--gain", type=float, default=None)
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--interval", type=float, default=None, help="Seconds between captures")
    parser.add_argument("--max-captures", type=int, default=None)
    parser.add_argument("--device-arg", action="append", default=None, help="SDR device arg key=value")
    parser.add_argument("--validate", action="store_true", help="Run a single capture and validate signal")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return run_pipeline(args)


if __name__ == "__main__":
    raise SystemExit(main())
