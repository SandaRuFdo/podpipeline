#!/usr/bin/env python3
"""
Topic Segmentation Script
Analyzes podcast audio to identify topic transitions and create 
a timestamped topic map for syncing visuals.

Usage:
    python segment_topics.py <audio_file> [options]
    
Options:
    --model         Model size: tiny, small, medium, large-v3 (default: medium)
    --language      Force language (e.g., de, en)
    --script        Path to podcast script for segment matching
    --output        Output file path (default: stdout)
"""

import argparse
import json
import sys
import os
import re

def format_time_short(seconds):
    """Convert seconds to MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def transcribe_audio(audio_path, model_size="medium", language=None):
    """Transcribe audio and return segments"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("ERROR: faster-whisper not installed. Run: pip install faster-whisper")
        sys.exit(1)
    
    print(f"Loading model '{model_size}'...", file=sys.stderr)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print(f"Transcribing '{audio_path}'...", file=sys.stderr)
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5
    )
    
    result = []
    for segment in segments:
        result.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
        print(f"  [{format_time_short(segment.start)}] {segment.text.strip()[:80]}", file=sys.stderr)
    
    return result, info

def detect_topic_changes(segments, gap_threshold=2.0, text_window=5):
    """
    Detect topic transitions based on:
    - Gaps/pauses between segments
    - Text content changes (keyword shifts)
    """
    topics = []
    current_topic_start = 0
    current_texts = []
    
    for i, seg in enumerate(segments):
        current_texts.append(seg["text"])
        
        # Check for natural breaks
        is_break = False
        
        if i < len(segments) - 1:
            gap = segments[i + 1]["start"] - seg["end"]
            if gap > gap_threshold:
                is_break = True
        
        if is_break or i == len(segments) - 1:
            topic_text = " ".join(current_texts)
            topics.append({
                "start": current_topic_start,
                "end": seg["end"],
                "text_preview": topic_text[:200],
                "segment_count": len(current_texts)
            })
            if i < len(segments) - 1:
                current_topic_start = segments[i + 1]["start"]
            current_texts = []
    
    return topics

def match_to_script(segments, script_path):
    """
    Match transcript segments against a podcast script to identify
    which script section is being spoken at each timestamp.
    """
    if not os.path.exists(script_path):
        print(f"WARNING: Script file not found: {script_path}", file=sys.stderr)
        return None
    
    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()
    
    # Extract section headers from script
    sections = []
    section_pattern = r'##\s+(?:═+\s+)?(\d+)\.\s+(.+?)(?:\s*\(.*?\))?\s*$'
    
    for match in re.finditer(section_pattern, script, re.MULTILINE):
        sections.append({
            "number": int(match.group(1)),
            "title": match.group(2).strip()
        })
    
    # Also look for SLIDE headers if it's a slide source doc
    slide_pattern = r'##\s+SLIDE\s+(\d+)\s+—\s+(.+?)$'
    for match in re.finditer(slide_pattern, script, re.MULTILINE):
        sections.append({
            "number": int(match.group(1)),
            "title": match.group(2).strip()
        })
    
    return sections

def generate_report(segments, info, topics, script_sections=None):
    """Generate a markdown topic map report"""
    lines = []
    lines.append("# 🎧 Audio Topic Segmentation Report")
    lines.append("")
    lines.append(f"**Duration:** {format_time_short(info.duration)}")
    lines.append(f"**Language:** {info.language}")
    lines.append(f"**Total segments:** {len(segments)}")
    lines.append(f"**Detected topics:** {len(topics)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    if script_sections:
        lines.append("## Script Sections Found")
        lines.append("")
        for sec in script_sections:
            lines.append(f"- **{sec['number']}.** {sec['title']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append("## Detected Topic Segments")
    lines.append("")
    lines.append("| # | Start | End | Duration | Preview |")
    lines.append("|---|-------|-----|----------|---------|")
    
    for i, topic in enumerate(topics, 1):
        start = format_time_short(topic["start"])
        end = format_time_short(topic["end"])
        dur = format_time_short(topic["end"] - topic["start"])
        preview = topic["text_preview"][:100].replace("|", "\\|")
        lines.append(f"| {i:02d} | {start} | {end} | {dur} | {preview}... |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Full Timestamped Transcript")
    lines.append("")
    
    for seg in segments:
        start = format_time_short(seg["start"])
        end = format_time_short(seg["end"])
        lines.append(f"**[{start} → {end}]** {seg['text']}")
        lines.append("")
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Segment audio by topics")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--model", default="medium",
                       choices=["tiny", "small", "medium", "large-v3"],
                       help="Whisper model size (default: medium)")
    parser.add_argument("--language", default=None, help="Force language")
    parser.add_argument("--script", default=None, help="Path to podcast script")
    parser.add_argument("--output", default=None, help="Output file path")
    parser.add_argument("--gap", type=float, default=2.0,
                       help="Gap threshold in seconds for topic detection (default: 2.0)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.audio_file):
        print(f"ERROR: File not found: {args.audio_file}")
        sys.exit(1)
    
    # Transcribe
    segments, info = transcribe_audio(
        args.audio_file,
        model_size=args.model,
        language=args.language
    )
    
    # Detect topic changes
    topics = detect_topic_changes(segments, gap_threshold=args.gap)
    
    # Match to script if provided
    script_sections = None
    if args.script:
        script_sections = match_to_script(segments, args.script)
    
    # Generate report
    report = generate_report(segments, info, topics, script_sections)
    
    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nSaved report to: {args.output}", file=sys.stderr)
    else:
        print(report)
    
    print(f"\nDone! Found {len(topics)} topic segments in {format_time_short(info.duration)} of audio.", file=sys.stderr)

if __name__ == "__main__":
    main()
