#!/usr/bin/env python3
"""
force_16x9.py — Force all images in a folder to exactly 1920×1080 (YouTube 16:9)

Uses ffmpeg to scale + pad images. Maintains aspect ratio and adds black bars
if needed, then crops to perfect 16:9. Run after generate_image step.

Usage:
    python scripts/force_16x9.py <visuals_folder>

Example:
    python scripts/force_16x9.py episodes/S01/E01_iran_War/4_visuals/

Output:
    Overwrites each .png in-place with 1920x1080 version.
    Saves original as <name>_orig.png if --keep-originals flag is used.
"""
import subprocess
import sys
from pathlib import Path


def force_16x9(image_path: Path, keep_original: bool = False) -> bool:
    """Convert a single image to 1920x1080 via ffmpeg scale+pad."""
    if keep_original:
        orig = image_path.with_name(image_path.stem + "_orig" + image_path.suffix)
        image_path.rename(orig)
        src = str(orig)
    else:
        # ffmpeg can't overwrite in-place so use a temp file
        src = str(image_path)
        tmp = image_path.with_name(image_path.stem + "_tmp.png")
        dst = str(tmp)
    
    dst_path = image_path if not keep_original else image_path
    dst = str(image_path.with_name(image_path.stem + "_16x9.png"))

    cmd = [
        "ffmpeg", "-y",
        "-i", src,
        # Scale to fit within 1920x1080 keeping aspect ratio, then pad to exact 1920x1080
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",
        "-q:v", "1",   # max quality
        dst
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [ERROR] ffmpeg failed on {image_path.name}: {result.stderr[-200:]}")
        return False

    # Replace original with the 16x9 version
    out = Path(dst)
    out.rename(image_path)
    print(f"  [OK] {image_path.name} → 1920x1080")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python force_16x9.py <visuals_folder> [--keep-originals]")
        sys.exit(1)

    folder = Path(sys.argv[1])
    keep = "--keep-originals" in sys.argv

    if not folder.exists():
        print(f"[ERROR] Folder not found: {folder}")
        sys.exit(1)

    images = sorted(list(folder.glob("*.png")) + list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")))
    
    if not images:
        print(f"[WARN] No images found in: {folder}")
        sys.exit(0)

    print(f"[force_16x9] Processing {len(images)} image(s) in {folder}")
    ok = 0
    for img in images:
        if "_orig" in img.stem or "_tmp" in img.stem:
            continue  # skip backup files
        if force_16x9(img, keep_original=keep):
            ok += 1

    print(f"\n[force_16x9] Done. {ok}/{len(images)} converted to 1920x1080.")


if __name__ == "__main__":
    main()
