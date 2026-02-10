#!/usr/bin/env python3
"""
Smart Compositor v2 - Professional AI Demo Generator

Stitches together:
1. Gemini-generated intro/outro scenes (Images)
2. Screen recordings (WebP/MP4)
3. Scene-specific voiceovers (MP3)
4. Background music (optional)

Produces a polished 1080p MP4 demo video.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict

# Add parent to path for config_loader
sys.path.insert(0, str(Path(__file__).parent))
from config_loader import load_config
from caption_generator import generate_captions, create_styled_ass_file


class SmartCompositor:
    """Professional Video Compositor using FFmpeg"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = output_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def create_video_from_image(
        self, 
        image_path: Path, 
        duration: float, 
        output_filename: str
    ) -> Path:
        """Create a video clip from a static image"""
        output_path = self.temp_dir / output_filename
        
        print(f"🎬 Creating image clip: {image_path.name} ({duration}s)")
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    def convert_webp_to_mp4(
        self,
        webp_path: Path,
        output_filename: str
    ) -> Path:
        """Convert WebP animation to MP4 (Robust: FFmpeg -> PIL fallback)"""
        output_path = self.temp_dir / output_filename
        
        print(f"🎬 Converting recording: {webp_path.name}")
        
        # Method 1: Try direct FFmpeg
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(webp_path),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
                str(output_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError:
            print("⚠️  Direct FFmpeg conversion failed. Switching to PIL frame extraction...")
        
        # Method 2: PIL Extraction -> FFmpeg
        try:
            from PIL import Image
            
            frames_dir = self.temp_dir / f"frames_{webp_path.stem}"
            frames_dir.mkdir(parents=True, exist_ok=True)
            
            with Image.open(webp_path) as im:
                # Extract frames
                frame_num = 0
                try:
                    while True:
                        frame_path = frames_dir / f"frame_{frame_num:04d}.png"
                        im.save(frame_path)
                        frame_num += 1
                        im.seek(frame_num)
                except EOFError:
                    pass # End of sequence
            
            print(f"   Extracted {frame_num} frames. Stitching...")
            
            # Stitch with FFmpeg
            # Assuming ~10 fps for these recordings, or we can calculate from duration
            fps = 10 
            
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(frames_dir / "frame_%04d.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
                str(output_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Cleanup frames
            for f in frames_dir.glob("*.png"):
                f.unlink()
            frames_dir.rmdir()
            
            return output_path
            
        except Exception as e:
            print(f"❌ Failed to convert WebP: {e}")
            raise e

    def overlay_audio(
        self,
        video_path: Path,
        audio_path: Path,
        output_filename: str,
        burn_captions: bool = False
    ) -> Path:
        """Overlay voiceover onto video, optionally burning captions"""
        output_path = self.temp_dir / output_filename
        
        # Get duration of audio
        audio_duration = self._get_duration(audio_path)
        video_duration = self._get_duration(video_path)
        
        print(f"🎵 Overlaying audio: {audio_path.name} ({audio_duration:.1f}s) on {video_path.name} ({video_duration:.1f}s)")
        
        # Prepare filters
        # 1. Pad video if needed [v_padded]
        filters = f"[0:v]tpad=stop_mode=clone:stop_duration={max(0, audio_duration - video_duration + 1)}[v_padded]"
        last_stream = "[v_padded]"
        
        # 2. Generate and burn captions if requested
        if burn_captions:
            try:
                # Generate SRT
                srt_path = generate_captions(str(audio_path), None, str(self.temp_dir / f"{audio_path.stem}.srt"))
                # Generate ASS (Styled)
                ass_path = create_styled_ass_file(srt_path, None, str(self.temp_dir / f"{audio_path.stem}.ass"))
                
                # Add subtitle filter
                # escape path for ffmpeg filter
                ass_path_escaped = str(ass_path).replace(":", "\\:").replace("'", "\\'")
                filters += f";{last_stream}subtitles='{ass_path_escaped}'[v_out]"
                last_stream = "[v_out]"
                print(f"   📝 Burnt captions from: {ass_path}")
            except Exception as e:
                print(f"   ⚠️  Caption generation failed: {e}")
                filters += f";{last_stream}null[v_out]" # Fallback acts as pass-through
                last_stream = "[v_out]"
        else:
             # Just map input to output name
             filters += f";{last_stream}null[v_out]"
             last_stream = "[v_out]"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex", filters,
            "-map", last_stream,
            "-map", "1:a",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    def _get_duration(self, file_path: Path) -> float:
        """Get duration of media file using ffprobe"""
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return float(result.stdout.strip())
        except:
            return 0.0

    def concat_clips(
        self,
        clips: List[Path],
        output_path: Path
    ):
        """Concatenate all video clips"""
        print(f"🎞️ Concatenating {len(clips)} clips into final video...")
        
        # Create input list file
        list_file = self.temp_dir / "concat_list.txt"
        with open(list_file, "w") as f:
            for clip in clips:
                f.write(f"file '{clip.absolute()}'\n")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Final video saved: {output_path}")
        print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")


def main():
    """Build the demo video"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compose Professional Demo Video")
    parser.add_argument("--recordings-dir", default="../INPUT/raw_recordings")
    parser.add_argument("--scenes-dir", default="../OUTPUT/scenes")
    parser.add_argument("--voiceover-dir", default="../OUTPUT/voiceover")
    parser.add_argument("--output", default="../OUTPUT/final_video/Final_Demo_Video.mp4")
    parser.add_argument("--storyline", help="Path to Storyline.md (optional context)")
    parser.add_argument("--captions", type=str, default="false", help="Enable caption generation (true/false)")
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent
    
    def resolve_path(p: str, base: Path) -> Path:
        path = Path(p)
        return path if path.is_absolute() else base / p

    recordings_dir = resolve_path(args.recordings_dir, base_dir)
    scenes_dir = resolve_path(args.scenes_dir, base_dir)
    vo_dir = resolve_path(args.voiceover_dir, base_dir)
    output_path = resolve_path(args.output, base_dir)
    
    burn_captions = args.captions.lower() == "true"
    
    compositor = SmartCompositor(output_path.parent)
    
    # 1. Prepare segments
    segments = []
    
    def check_assets(video: Path, audio: Path) -> bool:
        if not video.exists():
            print(f"❌ Video missing: {video}")
            return False
        if not audio.exists():
            print(f"❌ Audio missing: {audio}")
            return False
        if audio.stat().st_size < 100:
            print(f"❌ Audio too small/empty: {audio}")
            return False
        return True

    # Scene 1: Hook (Gemini Image + VO)
    print("\n🎬 Processing Scene 1: Hook")
    hook_img = scenes_dir / "hook_scene.png"
    hook_vo = vo_dir / "scene_1_vo.mp3"
    
    if check_assets(hook_img, hook_vo):
        duration = compositor._get_duration(hook_vo) + 1.0 
        video_clip = compositor.create_video_from_image(hook_img, duration, "scene_1_base.mp4")
        final_clip = compositor.overlay_audio(video_clip, hook_vo, "scene_1_final.mp4", burn_captions)
        segments.append(final_clip)
    else:
        print("⚠️  Skipping Scene 1")

    # Scene 2: Landing Page (Recording + VO)
    print("\n🎬 Processing Scene 2: Landing Page")
    # Match by scene number (MP4 or WebP)
    candidates = list(recordings_dir.glob("scene_2_*.mp4")) + \
                 list(recordings_dir.glob("scene_2_*.webp"))
    scene_2_rec = sorted(candidates, key=lambda p: p.stat().st_mtime)[-1] if candidates else None
    scene_2_vo = vo_dir / "scene_2_vo.mp3"

    if scene_2_rec and check_assets(scene_2_rec, scene_2_vo):
        # Handle MP4 vs WebP
        if scene_2_rec.suffix.lower() == ".mp4":
             base_clip = compositor.temp_dir / "scene_2_base.mp4"
             cmd = [
                "ffmpeg", "-y", "-i", str(scene_2_rec),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
                str(base_clip)
             ]
             subprocess.run(cmd, check=True)
        else:
             base_clip = compositor.convert_webp_to_mp4(scene_2_rec, "scene_2_base.mp4")
             
        final_clip = compositor.overlay_audio(base_clip, scene_2_vo, "scene_2_final.mp4", burn_captions)
        segments.append(final_clip)
    else:
        print("⚠️  Skipping Scene 2 (Assets missing)")

    # Scene 3: Demo (Recording + VO)
    print("\n🎬 Processing Scene 3: Live Demo")
    candidates = list(recordings_dir.glob("scene_3_*.mp4")) + \
                 list(recordings_dir.glob("scene_3_*.webp"))
    scene_3_rec = sorted(candidates, key=lambda p: p.stat().st_mtime)[-1] if candidates else None
    scene_3_vo = vo_dir / "scene_3_vo.mp3"
    
    if scene_3_rec and check_assets(scene_3_rec, scene_3_vo):
        if scene_3_rec.suffix.lower() == ".mp4" or scene_3_rec.suffix.lower() == ".mov":
            base_clip = compositor.temp_dir / "scene_3_base.mp4"
            cmd = [
                "ffmpeg", "-y", "-i", str(scene_3_rec),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
                str(base_clip)
            ]
            subprocess.run(cmd, check=True)
        else:
            base_clip = compositor.convert_webp_to_mp4(scene_3_rec, "scene_3_base.mp4")
            
        final_clip = compositor.overlay_audio(base_clip, scene_3_vo, "scene_3_final.mp4", burn_captions)
        segments.append(final_clip)
    else:
        print("⚠️  Skipping Scene 3 (Assets missing)")

    # Scene 4: Results (Recording + VO)
    print("\n🎬 Processing Scene 4: Results")
    candidates = list(recordings_dir.glob("scene_4_*.mp4")) + \
                 list(recordings_dir.glob("scene_4_*.webp")) + \
                 list(recordings_dir.glob("scene_4_*.png"))
        
    scene_4_rec = sorted(candidates, key=lambda p: p.stat().st_mtime)[-1] if candidates else None
    scene_4_vo = vo_dir / "scene_4_vo.mp3"
    
    if scene_4_rec and check_assets(scene_4_rec, scene_4_vo):
        if scene_4_rec.suffix == ".png":
             duration = compositor._get_duration(scene_4_vo) + 1.0
             base_clip = compositor.create_video_from_image(scene_4_rec, duration, "scene_4_base.mp4")
        else:
             base_clip = compositor.convert_webp_to_mp4(scene_4_rec, "scene_4_base.mp4")
             
        final_clip = compositor.overlay_audio(base_clip, scene_4_vo, "scene_4_final.mp4", burn_captions)
        segments.append(final_clip)
    else:
        print("⚠️  Skipping Scene 4 (Assets missing)")

    # Scene 5: Tech Wrap-up (Gemini Image + VO)
    print("\n🎬 Processing Scene 5: Tech Wrap-up")
    tech_img = scenes_dir / "tech_wrapup_scene.png"
    tech_vo = vo_dir / "scene_5_tech_vo.mp3"
    
    if check_assets(tech_img, tech_vo):
        duration = compositor._get_duration(tech_vo) + 2.0 
        video_clip = compositor.create_video_from_image(tech_img, duration, "scene_5_base.mp4")
        final_clip = compositor.overlay_audio(video_clip, tech_vo, "scene_5_final.mp4", burn_captions)
        segments.append(final_clip)
    else:
        print("⚠️  Skipping Scene 5")

    # Final Concatenation
    if segments:
        compositor.concat_clips(segments, output_path)
    else:
        print("❌ No segments to concatenate")


if __name__ == "__main__":
    main()
