"""
Caption Generator

Generates word-level captions from voiceover audio using Gemini Speech-to-Text.
Outputs both SRT and ASS formats for FFmpeg burning.
"""

import os
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

from config_loader import load_config, DemoConfig

# Load environment variables
load_dotenv()


class Caption:
    """Single caption with timing"""
    def __init__(self, index: int, start: float, end: float, text: str):
        self.index = index
        self.start = start
        self.end = end
        self.text = text
    
    def to_srt(self) -> str:
        """Convert to SRT format"""
        def format_time(seconds: float) -> str:
            """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        return f"{self.index}\n{format_time(self.start)} --> {format_time(self.end)}\n{self.text}\n"


def generate_captions(
    audio_path: str,
    config: DemoConfig,
    output_path: str = "../OUTPUT/captions/captions.srt"
) -> str:
    """
    Generate word-level captions from voiceover audio using Gemini Speech-to-Text API
    
    Args:
        audio_path: Path to voiceover MP3 file
        config: DemoConfig (not used but kept for consistency)
        output_path: Where to save SRT file
        
    Returns:
        Path to generated SRT file
    """
    
    print("📝 Generating captions with Gemini Speech-to-Text...")
    print(f"   Audio: {audio_path}")
    
    try:
        # Get Gemini API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        client = genai.Client(api_key=api_key)
        
        # Read audio file
        print("🎙️  Transcribing audio with Gemini Speech-to-Text...")
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        # Create audio part for Gemini
        audio_part = types.Part.from_bytes(
            data=audio_data,
            mime_type="audio/mpeg"
        )
        
        # Transcribe with Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "Transcribe this audio exactly as spoken. Output only the transcription text, no other commentary.",
                audio_part
            ]
        )
        
        transcription_text = response.text.strip()
        print(f"✅ Transcription complete: {len(transcription_text)} characters")
        
        # Estimate timing (since Gemini doesn't provide word-level timestamps)
        # We'll create captions in ~4-second chunks for readability
        words = transcription_text.split()
        words_per_caption = 8  # ~4 seconds at 145 WPM (145/60 * 4 ≈ 9.7 words)
        
        captions = []
        current_time = 0.0
        caption_duration = 4.0  # seconds per caption
        
        for i in range(0, len(words), words_per_caption):
            chunk = words[i:i + words_per_caption]
            caption_text = " ".join(chunk)
            
            captions.append(Caption(
                index=len(captions) + 1,
                start=current_time,
                end=current_time + caption_duration,
                text=caption_text
            ))
            
            current_time += caption_duration
        
        # Write SRT file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for caption in captions:
                f.write(caption.to_srt())
                f.write('\n')
        
        print(f"✅ Captions generated successfully!")
        print(f"   Saved to: {output_file}")
        print(f"   Total captions: {len(captions)}")
        print()
        
        return str(output_file)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def create_styled_ass_file(
    srt_path: str,
    config: DemoConfig,
    output_path: str = "../OUTPUT/captions/captions_styled.ass"
) -> str:
    """
    Convert SRT to ASS format with custom styling for FFmpeg burning
    
    ASS format allows font, color, position, and outline customization
    
    Args:
        srt_path: Path to SRT file
        config: DemoConfig with styling preferences
        output_path: Where to save ASS file
        
    Returns:
        Path to generated ASS file
    """
    
    # Read SRT file
    srt_content = Path(srt_path).read_text(encoding='utf-8')
    
    # Parse SRT
    import re
    caption_pattern = r'(\d+)\n([\d:,]+)\s+-->\s+([\d:,]+)\n(.*?)(?=\n\n|\Z)'
    matches = re.findall(caption_pattern, srt_content, re.DOTALL)
    
    # ASS Header with styling
    ass_header = """[Script Info]
Title: Product Demo Captions
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Bold,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Convert SRT timestamps to ASS format (H:MM:SS.cc)
    def srt_time_to_ass(srt_time: str) -> str:
        """Convert SRT time (HH:MM:SS,mmm) to ASS time (H:MM:SS.cc)"""
        time_part, millis = srt_time.split(',')
        centiseconds = int(millis) // 10
        return f"{time_part}.{centiseconds:02d}"
    
    # Build ASS events
    ass_events = []
    for idx, start, end, text in matches:
        start_ass = srt_time_to_ass(start.strip())
        end_ass = srt_time_to_ass(end.strip())
        text_clean = text.strip().replace('\n', ' ')
        
        # ASS dialogue line
        line = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text_clean}"
        ass_events.append(line)
    
    # Combine header and events
    ass_content = ass_header + '\n'.join(ass_events)
    
    # Write ASS file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(ass_content, encoding='utf-8')
    
    print(f"✅ Styled ASS file created!")
    print(f"   Saved to: {output_file}")
    print(f"   Style: Montserrat Bold, 48px, White with black outline")
    print()
    
    return str(output_file)


if __name__ == "__main__":
    import sys
    
    # Usage: python caption_generator.py [audio_path] [config_path]
    audio_path = sys.argv[1] if len(sys.argv) > 1 else "../OUTPUT/voiceover/voiceover_raw.mp3"
    config_path = sys.argv[2] if len(sys.argv) > 2 else "../INPUT/configuration/Product_Specs.md"
    
    try:
        config = load_config(config_path)
        
        # Generate SRT
        srt_path = generate_captions(audio_path, config)
        
        # Create styled ASS file
        ass_path = create_styled_ass_file(srt_path, config)
        
        print("✅ Captions ready for video composition!")
        print(f"   SRT: {srt_path}")
        print(f"   ASS: {ass_path}")
        print()
        print("   Next: python video_compositor.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
