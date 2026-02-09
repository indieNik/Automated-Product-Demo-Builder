#!/usr/bin/env python3
"""
Simplified Final Demo Video Compositor

Strategy: Use the Belmix raw ad as the primary video content and overlay voiceover + captions.
This is the most straightforward approach given we have a complete 4-minute backend generation recording.
"""

import subprocess
import os
from pathlib import Path

# Asset Paths
BASE_DIR = Path(__file__).parent.parent
RECORDINGS_DIR = BASE_DIR / "01_raw_recordings"
VOICEOVER = BASE_DIR / "03_voiceover" / "voiceover_raw.mp3"
CAPTIONS = BASE_DIR / "04_captions" / "captions_styled.ass"
OUTPUT_DIR = BASE_DIR / "06_final"
OUTPUT_FILE = OUTPUT_DIR / "Final_Demo_Video.mp4"

# Primary Video
BELMIX_AD = RECORDINGS_DIR / "belmix_raw_ad_gen_edited.mov"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_video_duration(video_path):
    """Get video duration in seconds"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def main():
    print("="*80)
    print("🎬 FINAL DEMO VIDEO COMPOSITION")
    print("="*80)
    print()
    print("Strategy: Use Belmix raw ad + voiceover overlay + captions")
    print()
    
    # Get durations
    video_duration = get_video_duration(BELMIX_AD)
    vo_duration = get_video_duration(VOICEOVER)
    
    print(f"📊 Video Duration: {video_duration:.1f}s ({video_duration/60:.1f} min)")
    print(f"📊 Voiceover Duration: {vo_duration:.1f}s ({vo_duration/60:.1f} min)")
    print()
    
    # Determine final duration (use shorter of the two)
    final_duration = min(video_duration, vo_duration)
    print(f"⏱️  Final Duration: {final_duration:.1f}s ({final_duration/60:.1f} min)")
    print()
    
    print("🎥 Composing final video...")
    print("   1. Trimming video to match voiceover length")
    print("   2. Adding voiceover audio track")
    print("   3. Burning in captions")
    print()
    
    # Single FFmpeg command: trim video, add voiceover, burn captions
    cmd = [
        "ffmpeg", "-y",
        "-i", str(BELMIX_AD),          # Video input
        "-i", str(VOICEOVER),          # Audio input
        "-t", str(final_duration),     # Trim to final duration
        "-filter_complex",
        f"[0:v]ass={CAPTIONS.absolute()}[v]",  # Burn captions
        "-map", "[v]",                  # Use filtered video
        "-map", "1:a",                  # Use voiceover audio
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        str(OUTPUT_FILE)
    ]
    
    print("Running FFmpeg...")
    subprocess.run(cmd, check=True)
    
    print()
    print("="*80)
    print("✅ FINAL DEMO VIDEO COMPLETE!")
    print("="*80)
    print(f"📁 Output: {OUTPUT_FILE}")
    print(f"📊 File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")
    
    final_output_duration = get_video_duration(OUTPUT_FILE)
    print(f"⏱️  Duration: {final_output_duration:.1f}s ({final_output_duration/60:.1f} min)")
    print()
    print("🎯 Ready for hackathon submission!")
    print()
    
    # Play the video
    print("▶️  To play the video:")
    print(f"   open '{OUTPUT_FILE}'")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
