"""
Video Compositor

Assembles final demo video using FFmpeg:
- Screen recording
- Voiceover audio
- Background music
- Burned captions
"""

import os
import subprocess
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from config_loader import load_config, DemoConfig

# Load environment variables
load_dotenv()


def check_ffmpeg_installed() -> bool:
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds using ffprobe"""
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"⚠️  Could not determine audio duration: {e}")
        return 180.0  # Default to 3 minutes


def composite_final_video(
    recording_path: str,
    voiceover_path: str,
    captions_path: str,
    bgm_path: Optional[str],
    config: DemoConfig,
    output_path: str = "../OUTPUT/final_video/product_demo_final.mp4"
) -> str:
    """
    Composite final video using FFmpeg
    
    Args:
        recording_path: Path to screen recording (WebM or MP4)
        voiceover_path: Path to voiceover audio (MP3)
        captions_path: Path to styled captions (ASS file)
        bgm_path: Optional path to background music (MP3)
        config: DemoConfig
        output_path: Where to save final video
        
    Returns:
        Path to final video file
    """
    
    # Check FFmpeg
    if not check_ffmpeg_installed():
        raise RuntimeError(
            "FFmpeg not found. Install with: brew install ffmpeg"
        )
    
    print("🎬 Compositing final video with FFmpeg...")
    print(f"   Recording: {recording_path}")
    print(f"   Voiceover: {voiceover_path}")
    print(f"   Captions: {captions_path}")
    print(f"   BGM: {bgm_path if bgm_path else 'None'}")
    print()
    
    # Get voiceover duration
    vo_duration = get_audio_duration(voiceover_path)
    print(f"   Voiceover duration: {vo_duration:.1f}s")
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Build FFmpeg command
    if bgm_path and Path(bgm_path).exists():
        # Complex audio mixing with sidechain compression
        cmd = [
            'ffmpeg',
            '-i', recording_path,    # Video input
            '-i', voiceover_path,    # Voiceover audio
            '-i', bgm_path,          # Background music
            '-filter_complex',
            f"""
            [1:a]volume=-6dB[vo];
            [2:a]volume=-20dB,afade=t=in:st=0:d=2,afade=t=out:st={vo_duration-3}:d=3[bgm];
            [vo][bgm]amix=inputs=2:duration=longest:normalize=0[audio]
            """.strip().replace('\n', ''),
            '-map', '0:v',           # Use video from input 0
            '-map', '[audio]',       # Use mixed audio
            '-vf', f"ass={captions_path}",  # Burn captions
            '-c:v', 'libx264',       # H.264 codec
            '-preset', 'medium',     # Encoding speed
            '-crf', '23',            # Quality (lower = better, 18-28 range)
            '-c:a', 'aac',           # AAC audio codec
            '-b:a', '192k',          # Audio bitrate
            '-t', str(config.demo.duration_seconds),  # Trim to exact duration
            '-y',                    # Overwrite output
            str(output_file)
        ]
    else:
        # Simple version without BGM
        cmd = [
            'ffmpeg',
            '-i', recording_path,
            '-i', voiceover_path,
            '-filter_complex',
            '[1:a]volume=-6dB[audio]',
            '-map', '0:v',
            '-map', '[audio]',
            '-vf', f"ass={captions_path}",
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-t', str(config.demo.duration_seconds),
            '-y',
            str(output_file)
        ]
    
    # Execute FFmpeg
    print("   Running FFmpeg... (this may take 2-5 minutes)")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"\n✅ Video composition complete!")
        print(f"   Saved to: {output_file}")
        
        # Get file size
        file_size_mb = output_file.stat().st_size / 1024 / 1024
        print(f"   File size: {file_size_mb:.2f} MB")
        
        # Verify duration
        final_duration = get_audio_duration(str(output_file))
        print(f"   Duration: {final_duration:.1f}s / {config.demo.duration_seconds}s target")
        
        if final_duration > config.demo.duration_seconds + 2:
            print(f"\n⚠️  WARNING: Video is {final_duration - config.demo.duration_seconds:.1f}s longer than target!")
        
        return str(output_file)
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ FFmpeg failed!")
        print(f"   Error: {e.stderr}")
        raise


def create_simple_composite(
    recording_path: str,
    output_path: str = "../OUTPUT/final_video/recording_only.mp4"
) -> str:
    """
    Create simple video from recording only (no audio or captions)
    Useful for testing or when voiceover is not ready
    """
    
    if not check_ffmpeg_installed():
        raise RuntimeError("FFmpeg not found")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        'ffmpeg',
        '-i', recording_path,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-an',  # Remove audio
        '-y',
        str(output_file)
    ]
    
    subprocess.run(cmd, check=True)
    
    print(f"✅ Simple video created: {output_file}")
    return str(output_file)


if __name__ == "__main__":
    import sys
    
    # Usage: python video_compositor.py [recording] [voiceover] [captions] [bgm] [config]
    recording = sys.argv[1] if len(sys.argv) > 1 else "../INPUT/raw_recordings/screen_recording.webm"
    voiceover = sys.argv[2] if len(sys.argv) > 2 else "../OUTPUT/voiceover/voiceover_raw.mp3"
    captions = sys.argv[3] if len(sys.argv) > 3 else "../OUTPUT/captions/captions_styled.ass"
    bgm = sys.argv[4] if len(sys.argv) > 4 else None
    config_path = sys.argv[5] if len(sys.argv) > 5 else "../INPUT/configuration/Product_Specs.json"
    
    try:
        config = load_config(config_path)
        
        final_video = composite_final_video(
            recording_path=recording,
            voiceover_path=voiceover,
            captions_path=captions,
            bgm_path=bgm,
            config=config
        )
        
        print("\n🎉 Demo video production complete!")
        print(f"   Final video: {final_video}")
        print()
        print("   Ready for submission!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
