#!/usr/bin/env python3
"""LavaSR v2 ablation test.

Creates synthetic clean audio at 48 kHz, degrades to 8 kHz / 16 kHz,
upsamples to 48 kHz, then compares quality before/after LavaSR with SNR and
log-spectral distance (LSD).

If LavaSR is unavailable, the script documents the install/runtime failure and
writes a report with baseline-only metrics.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "lavasr_ablation_output"
AUDIO_DIR = OUT_DIR / "audio"
RESULTS_JSON = OUT_DIR / "ablation_results.json"
RESULTS_MD = ROOT / "ablation_results.md"


@dataclass
class CaseResult:
    case_name: str
    input_sr: int
    lavasr_ok: bool
    lavasr_cmd: str | None
    lavasr_error: str | None
    snr_before_db: float
    snr_after_db: float | None
    lsd_before_db: float
    lsd_after_db: float | None


def write_wav(path: Path, samples: np.ndarray, sr: int) -> None:
    x = np.clip(samples, -1.0, 1.0)
    pcm = (x * 32767.0).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        n_ch = wf.getnchannels()
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        data = wf.readframes(n_frames)
    x = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
    if n_ch > 1:
        x = x.reshape(-1, n_ch).mean(axis=1)
    return x, int(sr)


def resample_linear(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out:
        return x.copy()
    if x.size == 0:
        return x.copy()
    n_out = max(1, int(round(x.size * float(sr_out) / float(sr_in))))
    t_in = np.linspace(0.0, 1.0, num=x.size, endpoint=False)
    t_out = np.linspace(0.0, 1.0, num=n_out, endpoint=False)
    return np.interp(t_out, t_in, x).astype(np.float32)


def compute_snr_db(reference: np.ndarray, estimate: np.ndarray) -> float:
    n = min(reference.size, estimate.size)
    if n == 0:
        return float("nan")
    r = reference[:n]
    e = estimate[:n]
    num = float(np.mean(r * r)) + 1e-12
    den = float(np.mean((r - e) ** 2)) + 1e-12
    return 10.0 * math.log10(num / den)


def stft_power(x: np.ndarray, n_fft: int = 1024, hop: int = 256) -> np.ndarray:
    if x.size < n_fft:
        x = np.pad(x, (0, n_fft - x.size))
    win = np.hanning(n_fft).astype(np.float32)
    frames = []
    for i in range(0, x.size - n_fft + 1, hop):
        seg = x[i : i + n_fft] * win
        spec = np.fft.rfft(seg)
        frames.append((spec.real**2 + spec.imag**2).astype(np.float32))
    if not frames:
        spec = np.fft.rfft(x[:n_fft] * win)
        frames = [spec.real**2 + spec.imag**2]
    return np.stack(frames, axis=0)


def compute_lsd_db(reference: np.ndarray, estimate: np.ndarray) -> float:
    n = min(reference.size, estimate.size)
    if n == 0:
        return float("nan")
    p_ref = stft_power(reference[:n]) + 1e-10
    p_est = stft_power(estimate[:n]) + 1e-10
    m = min(p_ref.shape[0], p_est.shape[0])
    p_ref = p_ref[:m]
    p_est = p_est[:m]
    log_ref = 10.0 * np.log10(p_ref)
    log_est = 10.0 * np.log10(p_est)
    return float(np.mean(np.sqrt(np.mean((log_ref - log_est) ** 2, axis=1))))


def gen_clean_signal(sr: int = 48000, seconds: float = 6.0) -> np.ndarray:
    t = np.arange(int(sr * seconds), dtype=np.float32) / float(sr)
    # Voice-like synthetic content: harmonics + slow envelope + broadband noise.
    f0 = 140.0 + 20.0 * np.sin(2.0 * np.pi * 0.4 * t)
    phase = np.cumsum(2.0 * np.pi * f0 / sr)
    carrier = (
        0.45 * np.sin(phase)
        + 0.22 * np.sin(2.0 * phase + 0.1)
        + 0.12 * np.sin(3.0 * phase + 0.2)
    )
    envelope = 0.65 + 0.35 * np.sin(2.0 * np.pi * 1.8 * t)
    hiss = 0.015 * np.random.default_rng(7).standard_normal(t.shape[0]).astype(np.float32)
    x = (carrier * envelope + hiss).astype(np.float32)
    return np.clip(x, -1.0, 1.0)


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def run_lavasr(input_wav: Path, output_wav: Path) -> tuple[bool, str | None, str | None]:
    py = shutil.which("python3") or sys.executable
    commands = [
        [py, "-m", "lavasr", "--input", str(input_wav), "--output", str(output_wav), "--model", "v2"],
        [py, "-m", "lavasr", "-i", str(input_wav), "-o", str(output_wav), "--model", "v2"],
        [py, "-m", "lavasr", str(input_wav), str(output_wav), "--model", "v2"],
    ]
    errors: list[str] = []
    for cmd in commands:
        code, out, err = run_cmd(cmd)
        if code == 0 and output_wav.exists() and output_wav.stat().st_size > 0:
            return True, " ".join(cmd), None
        errors.append(
            f"cmd={' '.join(cmd)} | exit={code} | stdout={out or '<empty>'} | stderr={err or '<empty>'}"
        )
    return False, None, "\n".join(errors)


def evaluate_case(clean_48k: np.ndarray, input_sr: int, case_name: str) -> CaseResult:
    clean_low = resample_linear(clean_48k, 48000, input_sr)
    low_path = AUDIO_DIR / f"{case_name}_{input_sr}hz_input.wav"
    out_path = AUDIO_DIR / f"{case_name}_{input_sr}hz_lavasr48k.wav"
    write_wav(low_path, clean_low, input_sr)

    before_up = resample_linear(clean_low, input_sr, 48000)
    snr_before = compute_snr_db(clean_48k, before_up)
    lsd_before = compute_lsd_db(clean_48k, before_up)

    ok, cmd, err = run_lavasr(low_path, out_path)
    if ok:
        enhanced, sr = read_wav(out_path)
        if sr != 48000:
            enhanced = resample_linear(enhanced, sr, 48000)
        snr_after = compute_snr_db(clean_48k, enhanced)
        lsd_after = compute_lsd_db(clean_48k, enhanced)
    else:
        snr_after = None
        lsd_after = None

    return CaseResult(
        case_name=case_name,
        input_sr=input_sr,
        lavasr_ok=ok,
        lavasr_cmd=cmd,
        lavasr_error=err,
        snr_before_db=snr_before,
        snr_after_db=snr_after,
        lsd_before_db=lsd_before,
        lsd_after_db=lsd_after,
    )


def fmt(v: float | None, digits: int = 3) -> str:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "N/A"
    return f"{v:.{digits}f}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7, help="Random seed for deterministic synthetic audio.")
    args = parser.parse_args()

    np.random.seed(args.seed)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    clean = gen_clean_signal(sr=48000, seconds=6.0)
    clean_path = AUDIO_DIR / "synthetic_clean_48k_reference.wav"
    write_wav(clean_path, clean, 48000)

    cases = [
        evaluate_case(clean, 8000, "synthetic_voice"),
        evaluate_case(clean, 16000, "synthetic_voice"),
    ]

    lavasr_available = any(c.lavasr_ok for c in cases)
    install_note = "LavaSR executable/module not available in environment." if not lavasr_available else "LavaSR ran successfully for at least one case."

    avg_snr_before = float(np.mean([c.snr_before_db for c in cases]))
    avg_lsd_before = float(np.mean([c.lsd_before_db for c in cases]))
    after_snrs = [c.snr_after_db for c in cases if c.snr_after_db is not None]
    after_lsds = [c.lsd_after_db for c in cases if c.lsd_after_db is not None]
    avg_snr_after = float(np.mean(after_snrs)) if after_snrs else None
    avg_lsd_after = float(np.mean(after_lsds)) if after_lsds else None

    results: dict[str, Any] = {
        "generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "python": sys.version.split()[0],
        "lavasr_available": lavasr_available,
        "install_note": install_note,
        "cases": [
            {
                "case_name": c.case_name,
                "input_sr": c.input_sr,
                "lavasr_ok": c.lavasr_ok,
                "lavasr_cmd": c.lavasr_cmd,
                "lavasr_error": c.lavasr_error,
                "snr_before_db": c.snr_before_db,
                "snr_after_db": c.snr_after_db,
                "lsd_before_db": c.lsd_before_db,
                "lsd_after_db": c.lsd_after_db,
            }
            for c in cases
        ],
        "averages": {
            "snr_before_db": avg_snr_before,
            "snr_after_db": avg_snr_after,
            "lsd_before_db": avg_lsd_before,
            "lsd_after_db": avg_lsd_after,
            "snr_delta_db": (avg_snr_after - avg_snr_before) if avg_snr_after is not None else None,
            "lsd_delta_db": (avg_lsd_after - avg_lsd_before) if avg_lsd_after is not None else None,
        },
    }

    RESULTS_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")

    lines = [
        "# LavaSR v2 Ablation Results",
        "",
        f"Generated: {results['generated_utc']}",
        "",
        "## Setup",
        "",
        "- Test inputs: synthetic voice-like audio, downsampled to 8 kHz and 16 kHz",
        "- Target output: 48 kHz",
        "- Baseline: linear interpolation upsample",
        "- Metrics: SNR (dB, higher is better), LSD (dB, lower is better)",
        f"- LavaSR status: {'available' if lavasr_available else 'unavailable'}",
        "",
        "## Results",
        "",
        "| Case | Input SR | LavaSR ran | SNR before | SNR after | LSD before | LSD after |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]

    for c in cases:
        lines.append(
            f"| {c.case_name} | {c.input_sr} | {c.lavasr_ok} | {fmt(c.snr_before_db)} | {fmt(c.snr_after_db)} | {fmt(c.lsd_before_db)} | {fmt(c.lsd_after_db)} |"
        )

    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Average SNR before: {fmt(avg_snr_before)} dB",
            f"- Average SNR after: {fmt(avg_snr_after)} dB",
            f"- Average SNR delta: {fmt(results['averages']['snr_delta_db'])} dB",
            f"- Average LSD before: {fmt(avg_lsd_before)} dB",
            f"- Average LSD after: {fmt(avg_lsd_after)} dB",
            f"- Average LSD delta: {fmt(results['averages']['lsd_delta_db'])} dB",
            "",
            "## Notes",
            "",
        ]
    )

    if not lavasr_available:
        lines.extend(
            [
                "- LavaSR install/runtime is blocked in this environment; CLI calls failed for all tested invocation patterns.",
                "- For production enhancement workloads, GPU inference is recommended; CPU-only runs can be too slow for real-time or batch throughput targets.",
                "- Install command attempted: `pip install \"torch>=2.2\" lavasr`.",
                "",
                "### LavaSR error logs",
                "",
            ]
        )
        for c in cases:
            lines.append(f"#### {c.case_name} @ {c.input_sr} Hz")
            lines.append("")
            lines.append("```text")
            lines.append(c.lavasr_error or "<no error>")
            lines.append("```")
            lines.append("")

    RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {RESULTS_JSON}")
    print(f"Wrote {RESULTS_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
