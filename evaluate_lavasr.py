#!/usr/bin/env python3
"""Run LavaSR v2 ablation on local audio samples."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
SAMPLES_DIR = ROOT / "audio_samples"
OUT_DIR = ROOT / "lavasr_eval_output"
ENHANCED_DIR = OUT_DIR / "enhanced"
RESULTS_JSON = OUT_DIR / "results.json"
RESULTS_MD = OUT_DIR / "results.md"
SUPPORTED_EXTS = {".wav", ".flac", ".mp3", ".m4a", ".ogg"}


@dataclass
class EvalSample:
    input_path: Path
    reference_path: Path | None
    reference_source: str


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def normalize_text(text: str) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9\s']", " ", (text or "").lower())
    return [w for w in cleaned.split() if w]


def levenshtein_distance(a: list[str], b: list[str]) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    dp = list(range(len(b) + 1))
    for i, aw in enumerate(a, start=1):
        prev = dp[0]
        dp[0] = i
        for j, bw in enumerate(b, start=1):
            cur = dp[j]
            if aw == bw:
                dp[j] = prev
            else:
                dp[j] = min(prev + 1, dp[j] + 1, dp[j - 1] + 1)
            prev = cur
    return dp[-1]


def compute_wer(reference: str, hypothesis: str) -> float | None:
    ref_words = normalize_text(reference)
    hyp_words = normalize_text(hypothesis)
    if not ref_words:
        return None
    distance = levenshtein_distance(ref_words, hyp_words)
    return float(distance) / float(len(ref_words))


def read_audio_mono(path: Path) -> tuple[np.ndarray, int]:
    try:
        import soundfile as sf

        data, sr = sf.read(str(path), always_2d=False)
        x = np.asarray(data, dtype=np.float32)
        if x.ndim > 1:
            x = x.mean(axis=1)
        return x, int(sr)
    except Exception:
        pass

    try:
        import librosa

        x, sr = librosa.load(str(path), sr=None, mono=True)
        return np.asarray(x, dtype=np.float32), int(sr)
    except Exception:
        pass

    if path.suffix.lower() != ".wav":
        raise RuntimeError(f"Could not decode non-WAV file without soundfile/librosa: {path}")

    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        sr = wf.getframerate()
        sw = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())

    if sw == 1:
        x = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        x = (x - 128.0) / 128.0
    elif sw == 2:
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sw == 4:
        x = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sw}")

    if channels > 1:
        x = x.reshape(-1, channels).mean(axis=1)
    return x, int(sr)


def resample_audio(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out:
        return x
    if x.size == 0:
        return x
    duration = x.size / float(sr_in)
    n_out = max(1, int(round(duration * sr_out)))
    t_in = np.linspace(0.0, duration, x.size, endpoint=False)
    t_out = np.linspace(0.0, duration, n_out, endpoint=False)
    return np.interp(t_out, t_in, x).astype(np.float32)


def align_pair(reference: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = min(reference.size, test.size)
    if n == 0:
        return np.array([], dtype=np.float32), np.array([], dtype=np.float32)
    return reference[:n].astype(np.float32), test[:n].astype(np.float32)


def compute_pesq_stoi(reference_path: Path, test_path: Path) -> dict[str, float | None]:
    try:
        from pesq import pesq
    except Exception:
        pesq = None

    try:
        from pystoi import stoi
    except Exception:
        stoi = None

    if pesq is None and stoi is None:
        return {"pesq": None, "stoi": None}

    ref, sr_ref = read_audio_mono(reference_path)
    tst, sr_tst = read_audio_mono(test_path)
    target_sr = 16000
    ref = resample_audio(ref, sr_ref, target_sr)
    tst = resample_audio(tst, sr_tst, target_sr)
    ref, tst = align_pair(ref, tst)
    if ref.size == 0:
        return {"pesq": None, "stoi": None}

    pesq_score = None
    stoi_score = None

    if pesq is not None:
        try:
            pesq_score = float(pesq(target_sr, ref, tst, "wb"))
        except Exception:
            pesq_score = None

    if stoi is not None:
        try:
            stoi_score = float(stoi(ref, tst, target_sr, extended=False))
        except Exception:
            stoi_score = None

    return {"pesq": pesq_score, "stoi": stoi_score}


def discover_samples(sample_dir: Path) -> list[EvalSample]:
    files = sorted(
        p for p in sample_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    )
    files_set = set(files)
    results: list[EvalSample] = []
    for path in files:
        stem = path.stem
        if stem.endswith("_PROPER"):
            continue

        reference_path = None
        source = "none"
        candidate_stems: list[str] = []
        if stem.endswith("_before"):
            base = stem[: -len("_before")]
            candidate_stems = [f"{base}_after_PROPER", f"{base}_after"]
        elif stem.endswith("_after"):
            candidate_stems = [f"{stem}_PROPER"]

        for candidate_stem in candidate_stems:
            for ext in SUPPORTED_EXTS:
                candidate = sample_dir / f"{candidate_stem}{ext}"
                if candidate in files_set:
                    reference_path = candidate
                    source = "paired-audio"
                    break
            if reference_path is not None:
                break

        results.append(
            EvalSample(input_path=path, reference_path=reference_path, reference_source=source)
        )
    return results


def create_whisper_model(model_size: str, device: str, compute_type: str):
    from faster_whisper import WhisperModel

    return WhisperModel(model_size, device=device, compute_type=compute_type)


def transcribe(model: Any, audio_path: Path) -> str:
    segments, _ = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=True,
        language=None,
    )
    chunks = [str(seg.text).strip() for seg in segments if str(seg.text).strip()]
    return " ".join(chunks).strip()


def run_lavasr_v2(input_path: Path, output_path: Path) -> tuple[bool, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    candidates: list[list[str]] = []
    if shutil.which("lavasr"):
        candidates.extend(
            [
                ["lavasr", "--input", str(input_path), "--output", str(output_path), "--model", "v2"],
                ["lavasr", "-i", str(input_path), "-o", str(output_path), "--model", "v2"],
                ["lavasr", str(input_path), str(output_path), "--model", "v2"],
            ]
        )
    candidates.extend(
        [
            [sys.executable, "-m", "lavasr", "--input", str(input_path), "--output", str(output_path), "--model", "v2"],
            [sys.executable, "-m", "lavasr", "-i", str(input_path), "-o", str(output_path), "--model", "v2"],
            [sys.executable, "-m", "lavasr", str(input_path), str(output_path), "--model", "v2"],
        ]
    )

    logs: list[str] = []
    for cmd in candidates:
        code, out, err = run_cmd(cmd)
        logs.append(
            f"$ {' '.join(cmd)}\nexit={code}\nstdout={out[:300] or '<empty>'}\nstderr={err[:300] or '<empty>'}"
        )
        if code == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return True, "\n\n".join(logs)
    return False, "\n\n".join(logs) if logs else "No LavaSR commands available."


def safe_round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def summarize_metric(items: list[dict[str, Any]], key_before: str, key_after: str) -> dict[str, Any]:
    deltas = []
    before_values = []
    after_values = []
    for item in items:
        b = item.get(key_before)
        a = item.get(key_after)
        if isinstance(b, (int, float)) and isinstance(a, (int, float)):
            before_values.append(float(b))
            after_values.append(float(a))
            deltas.append(float(a) - float(b))
    if not deltas:
        return {"count": 0, "avg_before": None, "avg_after": None, "avg_delta": None}
    return {
        "count": len(deltas),
        "avg_before": safe_round(float(np.mean(before_values))),
        "avg_after": safe_round(float(np.mean(after_values))),
        "avg_delta": safe_round(float(np.mean(deltas))),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# LavaSR v2 Ablation Results",
        "",
        f"Generated: {report['generated_at_utc']}",
        "",
        "## Summary",
        "",
        f"- Samples evaluated: **{summary['samples_total']}**",
        f"- Samples with LavaSR output: **{summary['samples_with_lavasr']}**",
        f"- Samples with reference transcripts for WER: **{summary['samples_with_wer']}**",
        f"- Average WER before: **{summary['wer']['avg_before']}**",
        f"- Average WER after: **{summary['wer']['avg_after']}**",
        f"- Average WER delta (after-before): **{summary['wer']['avg_delta']}**",
        f"- Average PESQ delta (after-before): **{summary['pesq']['avg_delta']}**",
        f"- Average STOI delta (after-before): **{summary['stoi']['avg_delta']}**",
        f"- Integration recommendation: **{summary['integration_recommendation']}**",
        "",
        "## Per-sample Results",
        "",
        "| Sample | LavaSR | WER before | WER after | PESQ before | PESQ after | STOI before | STOI after |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for item in report["samples"]:
        lines.append(
            f"| `{item['sample']}` | {item['lavasr_success']} | {item['wer_before']} | {item['wer_after']} | "
            f"{item['pesq_before']} | {item['pesq_after']} | {item['stoi_before']} | {item['stoi_after']} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- WER is computed from faster-whisper transcripts.",
            "- When explicit ground-truth text is unavailable, a paired cleaner sample transcript is used as proxy reference.",
            "- PESQ/STOI are included only when `pesq` and/or `pystoi` are installed.",
            "",
            "## LavaSR Invocation Logs",
            "",
            "```text",
            report.get("lavasr_logs", "No logs"),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="LavaSR v2 ablation test for audio enhancement")
    parser.add_argument("--sample-dir", default=str(SAMPLES_DIR), help="Directory containing audio samples")
    parser.add_argument("--model-size", default=os.getenv("LAVASR_EVAL_WHISPER_MODEL", "small"))
    parser.add_argument("--device", default=os.getenv("LAVASR_EVAL_WHISPER_DEVICE", "cpu"))
    parser.add_argument("--compute-type", default=os.getenv("LAVASR_EVAL_WHISPER_COMPUTE_TYPE", "int8"))
    args = parser.parse_args()

    sample_dir = Path(args.sample_dir).resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ENHANCED_DIR.mkdir(parents=True, exist_ok=True)

    install_cmd = [sys.executable, "-m", "pip", "install", "lavasr"]
    install_code, install_out, install_err = run_cmd(install_cmd)

    samples = discover_samples(sample_dir)
    if not samples:
        report = {
            "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "summary": {
                "samples_total": 0,
                "samples_with_lavasr": 0,
                "samples_with_wer": 0,
                "wer": {"count": 0, "avg_before": None, "avg_after": None, "avg_delta": None},
                "pesq": {"count": 0, "avg_before": None, "avg_after": None, "avg_delta": None},
                "stoi": {"count": 0, "avg_before": None, "avg_after": None, "avg_delta": None},
                "integration_recommendation": "no (no samples found)",
            },
            "samples": [],
            "environment": {
                "python": sys.version,
                "sample_dir": str(sample_dir),
            },
            "install_attempt": {
                "command": " ".join(install_cmd),
                "exit_code": install_code,
                "stdout": install_out,
                "stderr": install_err,
            },
            "lavasr_logs": "No samples found.",
        }
        RESULTS_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
        RESULTS_MD.write_text(render_markdown(report), encoding="utf-8")
        print(f"Wrote {RESULTS_JSON}")
        print(f"Wrote {RESULTS_MD}")
        return 0

    whisper_error = None
    model = None
    try:
        model = create_whisper_model(args.model_size, args.device, args.compute_type)
    except Exception as exc:
        whisper_error = str(exc)

    lavasr_logs: list[str] = []
    rows: list[dict[str, Any]] = []
    for sample in samples:
        row: dict[str, Any] = {
            "sample": str(sample.input_path.relative_to(ROOT)),
            "reference_audio": str(sample.reference_path.relative_to(ROOT)) if sample.reference_path else None,
            "reference_source": sample.reference_source,
            "lavasr_success": False,
            "wer_before": None,
            "wer_after": None,
            "wer_delta": None,
            "pesq_before": None,
            "pesq_after": None,
            "pesq_delta": None,
            "stoi_before": None,
            "stoi_after": None,
            "stoi_delta": None,
            "transcript_before": None,
            "transcript_after": None,
            "reference_text": None,
            "error": None,
        }

        try:
            enhanced_path = ENHANCED_DIR / f"{sample.input_path.stem}__lavasr_v2.wav"
            ok, log_text = run_lavasr_v2(sample.input_path, enhanced_path)
            row["lavasr_success"] = ok
            lavasr_logs.append(f"[{sample.input_path.name}]\n{log_text}")

            if model is None:
                row["error"] = f"faster-whisper unavailable: {whisper_error}"
                rows.append(row)
                continue

            transcript_before = transcribe(model, sample.input_path)
            row["transcript_before"] = transcript_before

            transcript_after = None
            if ok:
                transcript_after = transcribe(model, enhanced_path)
                row["transcript_after"] = transcript_after

            reference_text = None
            if sample.reference_path is not None:
                reference_text = transcribe(model, sample.reference_path)
                row["reference_text"] = reference_text

            if reference_text:
                w_before = compute_wer(reference_text, transcript_before)
                row["wer_before"] = safe_round(w_before)
                if transcript_after is not None:
                    w_after = compute_wer(reference_text, transcript_after)
                    row["wer_after"] = safe_round(w_after)
                    if w_before is not None and w_after is not None:
                        row["wer_delta"] = safe_round(w_after - w_before)

            if sample.reference_path is not None:
                before_quality = compute_pesq_stoi(sample.reference_path, sample.input_path)
                row["pesq_before"] = safe_round(before_quality["pesq"])
                row["stoi_before"] = safe_round(before_quality["stoi"])
                if ok:
                    after_quality = compute_pesq_stoi(sample.reference_path, enhanced_path)
                    row["pesq_after"] = safe_round(after_quality["pesq"])
                    row["stoi_after"] = safe_round(after_quality["stoi"])
                    if (
                        isinstance(row["pesq_before"], float)
                        and isinstance(row["pesq_after"], float)
                    ):
                        row["pesq_delta"] = safe_round(row["pesq_after"] - row["pesq_before"])
                    if (
                        isinstance(row["stoi_before"], float)
                        and isinstance(row["stoi_after"], float)
                    ):
                        row["stoi_delta"] = safe_round(row["stoi_after"] - row["stoi_before"])

        except Exception as exc:
            row["error"] = str(exc)
        rows.append(row)

    wer_summary = summarize_metric(rows, "wer_before", "wer_after")
    pesq_summary = summarize_metric(rows, "pesq_before", "pesq_after")
    stoi_summary = summarize_metric(rows, "stoi_before", "stoi_after")

    integration_recommendation = "no"
    if (
        wer_summary["count"] > 0
        and isinstance(wer_summary["avg_delta"], float)
        and wer_summary["avg_delta"] < 0
    ):
        integration_recommendation = "yes"

    report = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "summary": {
            "samples_total": len(rows),
            "samples_with_lavasr": sum(1 for r in rows if r["lavasr_success"]),
            "samples_with_wer": wer_summary["count"],
            "wer": wer_summary,
            "pesq": pesq_summary,
            "stoi": stoi_summary,
            "integration_recommendation": integration_recommendation,
        },
        "samples": rows,
        "environment": {
            "python": sys.version,
            "sample_dir": str(sample_dir),
            "whisper_model": args.model_size,
            "whisper_device": args.device,
            "whisper_compute_type": args.compute_type,
        },
        "install_attempt": {
            "command": " ".join(install_cmd),
            "exit_code": install_code,
            "stdout": install_out,
            "stderr": install_err,
        },
        "lavasr_logs": "\n\n".join(lavasr_logs),
    }

    RESULTS_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    RESULTS_MD.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {RESULTS_JSON}")
    print(f"Wrote {RESULTS_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
