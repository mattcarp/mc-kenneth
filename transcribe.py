#!/usr/bin/env python3
"""
CLI script for transcribing a local audio file with faster-whisper.
"""

import argparse
import json
import sys

from whisper_transcription import WhisperConfig, transcribe_audio_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe an audio file with faster-whisper large-v3."
    )
    parser.add_argument("audio_file", help="Path to WAV/MP3/M4A/etc audio file")
    parser.add_argument(
        "--model",
        default="large-v3",
        help="Whisper model size (default: large-v3)",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional language hint (e.g. en, it, mt)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full JSON instead of plain transcript text",
    )
    args = parser.parse_args()

    try:
        result = transcribe_audio_file(
            args.audio_file,
            WhisperConfig(model_size=args.model, language=args.language),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
