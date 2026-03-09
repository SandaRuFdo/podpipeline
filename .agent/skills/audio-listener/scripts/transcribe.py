#!/usr/bin/env python3
"""
Audio Transcription Script using faster-whisper
Transcribes audio files with precise timestamps.

Usage:
    python transcribe.py <audio_file> [options]

Options:
    --model    tiny | small | medium | large-v3 (default: small)
    --language Force language code e.g. de, en (auto-detect if omitted)
    --output   Output file path (stdout if omitted)
    --format   txt | srt | json | segments (default: segments)
    --words    Include word-level timestamps
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Read model choice saved by start.py (falls back to "small" if not set)
_config = Path(__file__).parent.parent.parent.parent.parent / ".agent" / "whisper_model.txt"
DEFAULT_MODEL = _config.read_text().strip() if _config.exists() else "small"


# ── TIME FORMATTERS ──────────────────────────────────────────────────────────

def fmt_short(s):
    """Seconds → MM:SS"""
    return f"{int(s//60):02d}:{int(s%60):02d}"

def fmt_full(s):
    """Seconds → HH:MM:SS.mmm"""
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int((s % 1) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d}.{ms:03d}"

def fmt_srt(s):
    """Seconds → SRT HH:MM:SS,mmm"""
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int((s % 1) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


# ── TRANSCRIPTION ────────────────────────────────────────────────────────────

def transcribe(audio_path, model_size=DEFAULT_MODEL, language=None, word_timestamps=False):
    """Transcribe audio and return (segments, info)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("ERROR: faster-whisper not installed. Run: pip install faster-whisper", file=sys.stderr)
        sys.exit(1)

    # Read device config saved by start.py; fall back to auto-detect
    _cfg_path = Path(__file__).parent.parent.parent.parent.parent / ".agent" / "device_config.json"
    if _cfg_path.exists():
        try:
            _cfg = json.load(open(_cfg_path))
            device  = _cfg.get("device", "cpu")
            compute = _cfg.get("compute_type", "int8")
            print(f"[transcribe] Using device from setup config: {_cfg.get('device_label', device)}", file=sys.stderr)
        except Exception:
            device, compute = "cpu", "int8"
    else:
        # Auto-detect fallback (no start.py config found)
        try:
            import torch
            device  = "cuda" if torch.cuda.is_available() else "cpu"
            compute = "float16" if device == "cuda" else "int8"
        except ImportError:
            device, compute = "cpu", "int8"

    print(f"[transcribe] Model: {model_size} | Device: {device} | Compute: {compute}", file=sys.stderr)
    print(f"[transcribe] Loading model...", file=sys.stderr)

    try:
        model = WhisperModel(model_size, device=device, compute_type=compute)

    except Exception as e:
        print(f"ERROR loading model '{model_size}': {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[transcribe] Transcribing: {audio_path}", file=sys.stderr)

    try:
        segments_gen, info = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=word_timestamps,
            beam_size=5,
            vad_filter=True,          # skip silence — faster + cleaner
            vad_parameters={"min_silence_duration_ms": 500}
        )
    except Exception as e:
        print(f"ERROR during transcription: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[transcribe] Language: {info.language} ({info.language_probability:.0%}) | Duration: {fmt_short(info.duration)}", file=sys.stderr)
    print(f"[transcribe] Processing segments...", file=sys.stderr)

    segments = []
    for seg in segments_gen:
        data = {
            "id":    seg.id,
            "start": seg.start,
            "end":   seg.end,
            "text":  seg.text.strip(),
        }
        if word_timestamps and seg.words:
            data["words"] = [
                {"word": w.word, "start": w.start, "end": w.end, "prob": round(w.probability, 3)}
                for w in seg.words
            ]
        segments.append(data)
        print(f"  [{fmt_short(seg.start)} -> {fmt_short(seg.end)}] {seg.text.strip()}", file=sys.stderr)

    print(f"[transcribe] Done. {len(segments)} segments.", file=sys.stderr)
    return segments, info


# ── OUTPUT FORMATTERS ────────────────────────────────────────────────────────

def out_segments(segs, info):
    lines = [
        f"# Transcript",
        f"# Duration: {fmt_short(info.duration)}",
        f"# Language: {info.language}  ({info.language_probability:.0%})",
        f"# Segments: {len(segs)}",
        "",
    ]
    for s in segs:
        lines.append(f"[{fmt_short(s['start'])} -> {fmt_short(s['end'])}]  {s['text']}")
        if "words" in s:
            lines.append("  " + " | ".join(f"{w['word']}@{fmt_short(w['start'])}" for w in s["words"]))
    return "\n".join(lines)


def out_srt(segs):
    lines = []
    for i, s in enumerate(segs, 1):
        lines += [str(i), f"{fmt_srt(s['start'])} --> {fmt_srt(s['end'])}", s["text"], ""]
    return "\n".join(lines)


def out_txt(segs):
    return "\n".join(s["text"] for s in segs)


def out_json(segs, info):
    return json.dumps({
        "duration": info.duration,
        "duration_fmt": fmt_short(info.duration),
        "language": info.language,
        "language_prob": round(info.language_probability, 3),
        "segments": segs
    }, ensure_ascii=False, indent=2)


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Transcribe audio with timestamps")
    p.add_argument("audio_file")
    p.add_argument("--model",    default=DEFAULT_MODEL, choices=["tiny","small","medium","large-v3"],
                   help=f"Whisper model (default: {DEFAULT_MODEL} — set during setup)")
    p.add_argument("--language", default=None)
    p.add_argument("--output",   default=None)
    p.add_argument("--format",   default="segments", choices=["txt","srt","json","segments"])
    p.add_argument("--words",    action="store_true", help="Word-level timestamps")
    args = p.parse_args()

    if not os.path.exists(args.audio_file):
        print(f"ERROR: File not found: {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    segs, info = transcribe(args.audio_file, args.model, args.language, args.words)

    fmt_map = {
        "segments": lambda: out_segments(segs, info),
        "srt":      lambda: out_srt(segs),
        "txt":      lambda: out_txt(segs),
        "json":     lambda: out_json(segs, info),
    }
    output = fmt_map[args.format]()

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[transcribe] Saved: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
