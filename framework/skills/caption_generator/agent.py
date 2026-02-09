#!/usr/bin/env python3
"""
Caption Generator Skill
=======================

Standalone agent for generating and burning captions onto videos.

Features:
- Converts SRT subtitles to ASS format for precise positioning
- Customizable font, size, color, and position
- Optimized for vertical (9:16) and horizontal (16:9) videos

Usage:
    from skills.caption_generator.agent import CaptionGenerator
    
    generator = CaptionGenerator()
    output_path = generator.burn_captions(
        video_path="input.mp4",
        caption_text="Hello, world!",
        position="bottom",
        font_size=100
    )
"""

import os
import subprocess
import tempfile
from typing import Optional, Literal


class CaptionGenerator:
    """
    Standalone caption generator that burns stylized subtitles onto videos.
    """
    
    def __init__(self):
        """Initialize the caption generator."""
        self.temp_dir = tempfile.gettempdir()
    
    def create_srt(
        self,
        text: str,
        duration: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create an SRT subtitle file.
        
        Args:
            text: Caption text to display
            duration: Duration of caption in seconds
            output_path: Path to save SRT file (optional, auto-generated if None)
        
        Returns:
            Path to created SRT file
        """
        if output_path is None:
            output_path = os.path.join(self.temp_dir, "caption.srt")
        
        # Convert duration to SRT time format
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        milliseconds = int((duration % 1) * 1000)
        
        end_time = f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        
        srt_content = f"""1
00:00:00,000 --> {end_time}
{text}
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        return output_path
    
    def srt_to_ass(
        self,
        srt_path: str,
        font_name: str = "Arial",
        font_size: int = 100,
        font_color: str = "yellow",
        bg_opacity: float = 0.55,
        position: Literal["top", "bottom", "center"] = "bottom",
        video_width: int = 1080,
        video_height: int = 1920,
        chunk_words: int = 0  # NEW: If > 0, split into chunks of N words
    ) -> str:
        """
        Convert SRT to ASS format with styling.
        
        Args:
            srt_path: Path to input SRT file
            font_name: Font family (default: Arial)
            font_size: Font size in pixels (default: 100)
            font_color: Font color name (default: yellow)
            bg_opacity: Background opacity 0-1 (default: 0.55)
            position: Vertical position (default: bottom)
            video_width: Video width in pixels (default: 1080)
            video_height: Video height in pixels (default: 1920)
            chunk_words: Split into chunks of N words (default: 0 = no chunking)
        
        Returns:
            Path to created ASS file
        """
        # Read SRT content
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        # Parse SRT (simple parser for single caption)
        lines = srt_content.strip().split('\n')
        caption_text = ""
        timing_line = ""
        
        for line in lines:
            if '-->' in line:
                timing_line = line
            elif not line.strip().isdigit() and line.strip() and '-->' not in line:
                caption_text = line.strip()
        
        if not timing_line:
            timing_line = "00:00:00,000 --> 00:00:10,000"
        
        start_time, end_time = timing_line.split(' --> ')
        
        # Convert SRT time to ASS time (HH:MM:SS,mmm -> H:MM:SS.mm)
        def srt_to_ass_time(srt_time):
            h, m, s_ms = srt_time.strip().split(':')
            s, ms = s_ms.split(',')
            return f"{int(h)}:{m}:{s}.{ms[:2]}"
        
        # Convert SRT time to seconds
        def srt_to_seconds(srt_time):
            h, m, s_ms = srt_time.strip().split(':')
            s, ms = s_ms.split(',')
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        
        # Convert seconds to ASS time
        def seconds_to_ass_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 100)
            return f"{h}:{m:02d}:{s:02d}.{ms:02d}"
        
        start_ass = srt_to_ass_time(start_time)
        end_ass = srt_to_ass_time(end_time)
        
        # Calculate total duration
        start_seconds = srt_to_seconds(start_time)
        end_seconds = srt_to_seconds(end_time)
        total_duration = end_seconds - start_seconds
        
        # Set positioning
        if position == "top":
            alignment = 8  # Top-center
            margin_v = 50
        elif position == "bottom":
            alignment = 2  # Bottom-center
            margin_v = 180  # Clearance from controls
        else:  # center
            alignment = 5  # Middle-center
            margin_v = 0
        
        # Convert bg_opacity to ASS alpha
        bg_alpha = int((1 - bg_opacity) * 255)
        
        # Color mapping (ASS uses AABBGGRR format)
        color_map = {
            "white": "FFFFFF",
            "yellow": "00FFFF",
            "red": "0000FF",
            "green": "00FF00",
            "blue": "FF0000"
        }
        text_color = color_map.get(font_color.lower(), "FFFFFF")
        
        # Create dialogue events
        dialogue_events = []
        
        if chunk_words > 0:
            # Split caption into word chunks
            words = caption_text.split()
            chunks = [' '.join(words[i:i+chunk_words]) for i in range(0, len(words), chunk_words)]
            
            # Calculate timing for each chunk
            chunk_duration = total_duration / len(chunks)
            
            for i, chunk in enumerate(chunks):
                chunk_start = start_seconds + (i * chunk_duration)
                chunk_end = chunk_start + chunk_duration
                
                chunk_start_ass = seconds_to_ass_time(chunk_start)
                chunk_end_ass = seconds_to_ass_time(chunk_end)
                
                dialogue_events.append(
                    f"Dialogue: 0,{chunk_start_ass},{chunk_end_ass},Default,,0,0,0,,{chunk}"
                )
        else:
            # Single caption
            dialogue_events.append(
                f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{caption_text}"
            )
        
        # Create ASS content
        ass_content = f"""[Script Info]
Title: Generated Subtitles
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00{text_color},&H00{text_color},&H00000000,&H{bg_alpha:02X}000000,-1,0,0,0,100,100,0,0,1,2,1,{alignment},108,108,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{chr(10).join(dialogue_events)}
"""
        
        # Write ASS file
        ass_path = srt_path.replace('.srt', '.ass')
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        return ass_path
    
    def burn_captions(
        self,
        video_path: str,
        caption_text: str,
        output_path: Optional[str] = None,
        font_name: str = "Arial",
        font_size: int = 100,
        font_color: str = "yellow",
        bg_opacity: float = 0.55,
        position: Literal["top", "bottom", "center"] = "bottom",
        duration: Optional[float] = None,
        chunk_words: int = 0  # NEW: Split into chunks of N words (0 = no chunking)
    ) -> str:
        """
        Burn captions onto video.
        
        Args:
            video_path: Input video file path
            caption_text: Text to display as caption
            output_path: Output video path (optional, auto-generated if None)
            font_name: Font family (default: Arial)
            font_size: Font size in pixels (default: 100)
            font_color: Font color (default: yellow)
            bg_opacity: Background opacity 0-1 (default: 0.55)
            position: Vertical position (default: bottom)
            duration: Caption duration in seconds (optional, uses video duration if None)
            chunk_words: Split caption into chunks of N words (default: 0 = show all at once)
                         Example: chunk_words=2 for TikTok-style 2-word chunks
        
        Returns:
            Path to output video with burned captions
        """
        # Get video duration if not provided
        if duration is None:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True,
                text=True
            )
            duration = float(result.stdout.strip())
        
        # Create SRT file
        srt_path = os.path.join(self.temp_dir, "caption.srt")
        self.create_srt(caption_text, duration, srt_path)
        
        # Convert to ASS
        ass_path = self.srt_to_ass(
            srt_path,
            font_name=font_name,
            font_size=font_size,
            font_color=font_color,
            bg_opacity=bg_opacity,
            position=position,
            chunk_words=chunk_words  # Pass through chunk_words
        )
        
        # Generate output path if not provided
        if output_path is None:
            base, ext = os.path.splitext(video_path)
            output_path = f"{base}_captioned{ext}"
        
        # Escape ASS path for FFmpeg
        ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
        
        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"ass={ass_escaped}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "copy",
            output_path
        ]
        
        print(f"🎬 Burning captions: {position} | {font_size}px | {font_color}")
        
        # Run FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        
        print(f"✅ Captions burned successfully: {output_path}")
        
        # Cleanup temp files
        if os.path.exists(srt_path):
            os.remove(srt_path)
        if os.path.exists(ass_path):
            os.remove(ass_path)
        
        return output_path


if __name__ == "__main__":
    # Quick test
    generator = CaptionGenerator()
    print("Caption Generator Agent Ready!")
    print("Usage: generator.burn_captions(video_path, caption_text, ...)")
