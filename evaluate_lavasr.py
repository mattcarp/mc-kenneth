#!/usr/bin/env python3
"""Evaluate LavaSR v2 audio enhancement and emit a markdown report."""

from __future__ import annotations

import argparse
import datetime as dt
import math
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
SAMPLES_DIR = ROOT / "audio_samples"
REPORT_PATH = ROOT / "LAVASR_EVALUATION.md"
WORK_DIR = ROOT / "lavasr_eval_output"


SUPPORTED_SAMPLE_EXTS = {".wav", ".flac", ".mp3", ".m4a", ".ogg"}


INSTALL_ATTEMPT_LOG = (
    "Attempted install commands:\n"
    "1) python3 -m pip install lavasr\n"
    "   -> failed with PEP 668 (externally-managed-environment).\n"
    "2) python3 -m venv .venv && .venv/bin/pip install lavasr\n"
    "   -> failed: DNS resolution error to package index and 'No matching distribution found for lavasr'."
)


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def pick_input_audio(explicit_input: str | None) -> tuple[Path, str]:
    if explicit_input:
        p = Path(explicit_input).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Input audio does not exist: {p}")
        return p, "user-provided"

    if SAMPLES_DIR.exists():
        candidates: list[Path] = []
        for ext in SUPPORTED_SAMPLE_EXTS:
            candidates.extend(sorted(SAMPLES_DIR.glob(f"*{ext}")))
        wavs = [c for c in candidates if c.suffix.lower() == ".wav"]
        if wavs:
            return wavs[0], "audio_samples (wav)"

    return create_synthetic_signal(), "synthetic"


def create_synthetic_signal() -> Path:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out = WORK_DIR / "synthetic_input.wav"

    sr = 16000
    duration_s = 3.0
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)

    tone = (
        0.45 * np.sin(2 * np.pi * 440 * t)
        + 0.25 * np.sin(2 * np.pi * 1200 * t)
        + 0.15 * np.sin(2 * np.pi * 3200 * t)
    )

    rng = np.random.default_rng(28)
    noise = 0.03 * rng.standard_normal(t.shape)
    x = np.clip(tone + noise, -1.0, 1.0)

    pcm = (x * 32767).astype(np.int16)
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())

    return out


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        nch = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sr = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    if sampwidth == 1:
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        data = (data - 128.0) / 128.0
    elif sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sampwidth}")

    if nch > 1:
        data = data.reshape(-1, nch).mean(axis=1)

    return data, sr


def resample_to_length(y: np.ndarray, n_out: int) -> np.ndarray:
    if len(y) == n_out:
        return y
    x_old = np.linspace(0, 1, len(y), endpoint=False)
    x_new = np.linspace(0, 1, n_out, endpoint=False)
    return np.interp(x_new, x_old, y)


def estimate_snr_db(reference: np.ndarray, test: np.ndarray) -> float:
    if len(reference) == 0 or len(test) == 0:
        return float("nan")
    y = resample_to_length(test, len(reference))

    denom = float(np.dot(y, y))
    if denom <= 1e-12:
        return float("nan")

    alpha = float(np.dot(reference, y) / denom)
    aligned = alpha * y
    err = reference - aligned

    p_sig = float(np.mean(reference**2))
    p_err = float(np.mean(err**2))
    if p_err <= 1e-12:
        return float("inf")
    return 10.0 * math.log10(max(p_sig, 1e-12) / p_err)


def attempt_lavasr(input_audio: Path, output_audio: Path) -> tuple[bool, str, str]:
    candidates = []

    if shutil.which("lavasr"):
        candidates.extend(
            [
                ["lavasr", "--input", str(input_audio), "--output", str(output_audio), "--model", "v2"],
                ["lavasr", "-i", str(input_audio), "-o", str(output_audio), "--model", "v2"],
                ["lavasr", str(input_audio), str(output_audio), "--model", "v2"],
            ]
        )

    candidates.extend(
        [
            [sys.executable, "-m", "lavasr", "--input", str(input_audio), "--output", str(output_audio), "--model", "v2"],
            [sys.executable, "-m", "lavasr", "-i", str(input_audio), "-o", str(output_audio), "--model", "v2"],
            [sys.executable, "-m", "lavasr", str(input_audio), str(output_audio), "--model", "v2"],
        ]
    )

    attempts: list[str] = []
    for cmd in candidates:
        code, out, err = run_cmd(cmd)
        attempts.append(
            f"$ {' '.join(cmd)}\\n"
            f"exit={code}\\n"
            f"stdout={out[:600] if out else '<empty>'}\\n"
            f"stderr={err[:600] if err else '<empty>'}"
        )
        if code == 0 and output_audio.exists() and output_audio.stat().st_size > 0:
            return True, "success", "\n\n".join(attempts)

    return False, "LavaSR invocation failed", "\n\n".join(attempts)


def build_report(
    input_audio: Path,
    input_origin: str,
    output_audio: Path,
    lavasr_ok: bool,
    lavasr_status: str,
    lavasr_logs: str,
    metrics: dict[str, str],
) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# LavaSR v2 Evaluation",
        "",
        f"Generated: {now}",
        "",
        "## Summary",
        "",
    ]

    if lavasr_ok:
        lines.append("- LavaSR v2 processing executed successfully.")
    else:
        lines.append("- LavaSR v2 processing did not complete in this environment.")

    lines.extend(
        [
            f"- Input source: `{input_origin}`",
            f"- Input file: `{input_audio}`",
            f"- Output file: `{output_audio}`",
            "",
            "## Installation Notes",
            "",
            "```text",
            INSTALL_ATTEMPT_LOG,
            "```",
            "",
            "## LavaSR Execution",
            "",
            f"Status: **{lavasr_status}**",
            "",
            "```text",
            lavasr_logs if lavasr_logs else "No invocation logs.",
            "```",
            "",
            "## Before/After Metrics",
            "",
            "| Metric | Before | After |",
            "|---|---:|---:|",
            f"| File size (bytes) | {metrics['before_size']} | {metrics['after_size']} |",
            f"| Sample rate (Hz) | {metrics['before_sr']} | {metrics['after_sr']} |",
            f"| Basic SNR estimate (dB) | n/a | {metrics['snr_db']} |",
            "",
            "## Findings",
            "",
        ]
    )

    if lavasr_ok:
        lines.extend(
            [
                "- Upsampling completed and metrics were computed from the produced output.",
                "- SNR estimate is scale-aligned and resampled, so treat it as a rough signal similarity indicator.",
            ]
        )
    else:
        lines.extend(
            [
                "- `pip install lavasr` failed due environment/package-index constraints, so LavaSR v2 could not be executed here.",
                "- Script generated a synthetic WAV fallback input and still recorded baseline metrics and failure logs.",
                "- Re-run in an environment with PyPI access and a resolvable `lavasr` package to complete a true before/after benchmark.",
            ]
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate LavaSR v2 audio enhancement")
    parser.add_argument("--input", help="Optional input audio file")
    args = parser.parse_args()

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    input_audio, input_origin = pick_input_audio(args.input)
    output_audio = WORK_DIR / "lavasr_v2_output.wav"

    lavasr_ok, lavasr_status, lavasr_logs = attempt_lavasr(input_audio, output_audio)

    before_size = input_audio.stat().st_size if input_audio.exists() else 0
    after_size = output_audio.stat().st_size if output_audio.exists() else 0

    before_sr = "n/a"
    after_sr = "n/a"
    snr_db = "n/a"

    try:
        if input_audio.suffix.lower() == ".wav":
            x, sr_x = read_wav(input_audio)
            before_sr = str(sr_x)

            if output_audio.exists() and output_audio.suffix.lower() == ".wav":
                y, sr_y = read_wav(output_audio)
                after_sr = str(sr_y)
                snr = estimate_snr_db(x, y)
                if math.isfinite(snr):
                    snr_db = f"{snr:.2f}"
                elif math.isinf(snr):
                    snr_db = "inf"
                else:
                    snr_db = "nan"
    except Exception as exc:
        lavasr_status = f"{lavasr_status}; metric read error: {exc}"

    metrics = {
        "before_size": str(before_size),
        "after_size": str(after_size),
        "before_sr": before_sr,
        "after_sr": after_sr,
        "snr_db": snr_db,
    }

    report = build_report(
        input_audio=input_audio,
        input_origin=input_origin,
        output_audio=output_audio,
        lavasr_ok=lavasr_ok,
        lavasr_status=lavasr_status,
        lavasr_logs=lavasr_logs,
        metrics=metrics,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
