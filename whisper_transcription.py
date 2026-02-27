#!/usr/bin/env python3
"""
Whisper transcription helpers for Kenneth RF captures.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WhisperConfig:
    model_size: str = "large-v3"
    device: str = "auto"
    compute_type: str = "default"
    beam_size: int = 5
    vad_filter: bool = True
    language: Optional[str] = None


class WhisperDependencyError(RuntimeError):
    """Raised when faster-whisper is not installed."""


def transcribe_audio_file(
    audio_file_path: str | Path,
    config: Optional[WhisperConfig] = None,
) -> Dict[str, Any]:
    """
    Transcribe an audio file with faster-whisper and return structured output.
    """
    cfg = config or WhisperConfig()
    path = Path(audio_file_path)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise WhisperDependencyError(
            "faster-whisper is not installed. Install with: pip install faster-whisper"
        ) from exc

    model = WhisperModel(
        cfg.model_size,
        device=cfg.device,
        compute_type=cfg.compute_type,
    )

    segments, info = model.transcribe(
        str(path),
        beam_size=cfg.beam_size,
        vad_filter=cfg.vad_filter,
        language=cfg.language,
    )

    segment_list: List[Dict[str, Any]] = []
    text_chunks: List[str] = []
    for segment in segments:
        seg_text = segment.text.strip()
        if not seg_text:
            continue
        segment_list.append(
            {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": seg_text,
            }
        )
        text_chunks.append(seg_text)

    return {
        "text": " ".join(text_chunks).strip(),
        "segments": segment_list,
        "language": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "model": cfg.model_size,
    }
