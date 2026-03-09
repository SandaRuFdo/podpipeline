#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_gpu_support.py — Installs PyTorch with CUDA 11.8 for NVIDIA GPUs (like GTX 1050)

faster-whisper needs the large PyTorch CUDA libraries to run on a dedicated GPU.
Run this script to automatically install the correct versions.
"""

import subprocess
import sys

def main():
    print("\n========================================================")
    print("  PodPipeline -- NVIDIA GPU Support Installer")
    print("========================================================\n")
    
    print("This will install PyTorch with CUDA 11.8 support.")
    print("WARNING: This is a ~2.5 GB download.")
    print("It is required to use your GTX 1050 for fast audio transcription.\n")
    
    try:
        reply = input("Do you want to proceed with the download? (y/n): ").strip().lower()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
        
    if reply != 'y':
        print("\nSkipping GPU support installation. Whisper will continue to use the CPU.")
        sys.exit(0)
        
    print("\n--> Starting download and installation (this may take a few minutes)...\n")
    
    # Run the pip install command for torch with cu118
    # We uninstall any existing torch first just to be safe
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision", "torchaudio"], capture_output=True)
    
    cmd = [
        sys.executable, "-m", "pip", "install",
        "torch", "torchvision", "torchaudio",
        "--index-url", "https://download.pytorch.org/whl/cu118"
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n  [OK]  NVIDIA GPU Support (PyTorch+CUDA) installed successfully!")
        print("        You can now re-run `python start.py` to auto-detect your GPU.")
    else:
        print("\n  [X]   Installation failed. Please check your internet connection or run the command manually:")
        print("        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118\n")


if __name__ == "__main__":
    main()
