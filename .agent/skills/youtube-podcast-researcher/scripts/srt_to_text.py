"""
SRT to Clean Text Converter
Strips timestamps, sequence numbers, and HTML tags from .srt subtitle files.
Outputs clean text ready for NotebookLM source ingestion.

Usage:
    python srt_to_text.py "input.srt"                    # → input.txt
    python srt_to_text.py "input.srt" "output.txt"       # → output.txt
    python srt_to_text.py ./research/*.srt                # batch mode
"""

import re
import sys
import glob
from pathlib import Path


def srt_to_text(srt_path: str) -> str:
    """Convert an SRT subtitle file to clean, readable text."""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    text_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip sequence numbers (just digits)
        if re.match(r"^\d+$", line):
            continue
        # Skip timestamp lines
        if re.match(r"\d{2}:\d{2}:\d{2}", line):
            continue
        # Remove HTML tags (common in auto-generated subs)
        line = re.sub(r"<[^>]+>", "", line)
        # Remove [Music], [Applause], etc.
        line = re.sub(r"\[.*?\]", "", line).strip()
        if line:
            text_lines.append(line)

    # Deduplicate consecutive identical lines (common in auto-subs)
    deduped = []
    for line in text_lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    return " ".join(deduped)


def main():
    if len(sys.argv) < 2:
        print("Usage: python srt_to_text.py <input.srt> [output.txt]")
        print("       python srt_to_text.py ./research/*.srt  (batch mode)")
        sys.exit(1)

    # Expand glob patterns (for batch mode)
    input_files = []
    for arg in sys.argv[1:]:
        expanded = glob.glob(arg)
        if expanded:
            input_files.extend(expanded)
        else:
            input_files.append(arg)

    # Filter to only .srt files
    srt_files = [f for f in input_files if f.endswith(".srt")]

    if not srt_files:
        # Single file with explicit output
        srt_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else srt_file.replace(".srt", ".txt")
        text = srt_to_text(srt_file)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✅ Converted: {output_file} ({len(text):,} chars)")
    else:
        # Batch mode
        for srt_file in srt_files:
            output_file = srt_file.replace(".srt", ".txt")
            text = srt_to_text(srt_file)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"✅ {Path(srt_file).name} → {Path(output_file).name} ({len(text):,} chars)")
        print(f"\n🎉 Converted {len(srt_files)} files")


if __name__ == "__main__":
    main()
