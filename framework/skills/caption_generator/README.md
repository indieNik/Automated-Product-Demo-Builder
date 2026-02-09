# Caption Generator Skill

Standalone agent for generating and burning stylized captions onto videos.

## Features

- ✨ **ASS Subtitle Format**: Precise positioning control (top/bottom/center)
- 🎨 **Customizable Styling**: Font, size, color, background opacity
- 📐 **Multi-Resolution Support**: Optimized for vertical (9:16) and horizontal (16:9)
- 🚀 **FFmpeg Powered**: Fast, high-quality caption burning
- 🔌 **Plug-and-Play**: Zero configuration, works out of the box
- 💬 **Chunked Captions**: TikTok/Reels style 2-3 word progressive display

## Quick Start

```python
from skills.caption_generator.agent import CaptionGenerator

# Initialize generator
generator = CaptionGenerator()

# Burn captions onto video
output_path = generator.burn_captions(
    video_path="input.mp4",
    caption_text="Bengaluru, here we come!",
    position="bottom",      # "top", "bottom", or "center"
    font_size=100,         # Pixels
    font_color="yellow"    # "yellow", "white", "red", "green", "blue"
)

print(f"✅ Output: {output_path}")
```

## TikTok-Style Chunked Captions

```python
# Progressive 2-word chunks (like TikTok/Reels)
output = generator.burn_captions(
    video_path="input.mp4",
    caption_text="Welcome to the best cafe in Bengaluru!",
    chunk_words=2,  # Show 2 words at a time
    position="bottom"
)

# Result: "Welcome to" → "the best" → "cafe in" → "Bengaluru!"
```

## API Reference

### `CaptionGenerator.burn_captions()`

Main method to burn captions onto a video.

**Parameters:**
- **video_path** (`str`): Input video file path
- **caption_text** (`str`): Text to display as caption
- **output_path** (`str`, optional): Output video path (auto-generated if None)
- **font_name** (`str`, default=`"Arial"`): Font family
- **font_size** (`int`, default=`100`): Font size in pixels
- **font_color** (`str`, default=`"yellow"`): Color name
- **bg_opacity** (`float`, default=`0.55`): Background opacity (0-1)
- **position** (`str`, default=`"bottom"`): Vertical position
- **duration** (`float`, optional): Caption duration in seconds
- **chunk_words** (`int`, default=`0`): Split into N-word chunks (0 = show all at once)

**Returns:** `str` - Path to output video with burned captions

### Font Size Guide (for 1920px height video)

- **60-80px**: Subtle, minimal
- **90-110px**: Clear & readable ⭐ **Recommended**
- **120-140px**: Bold & prominent (TikTok/Reels style)

### Chunking Guide

- **chunk_words=0**: Show full caption (default)
- **chunk_words=1**: One word at a time (very dynamic)
- **chunk_words=2**: Two words (TikTok style) ⭐ **Recommended**
- **chunk_words=3**: Three words (balanced readability)

## Dependencies

- FFmpeg (must be installed and in PATH)
- Python 3.7+

## Example Output

**Input:** `video.mp4` + `"Welcome to the best cafe in Bengaluru!"`  
**Output (chunk_words=2):**
- 0.0s - 1.5s: "Welcome to"
- 1.5s - 3.0s: "the best"
- 3.0s - 4.5s: "cafe in"
- 4.5s - 6.0s: "Bengaluru!"

## Integration

Use in your project:

```python
# Add to your video pipeline
from skills.caption_generator.agent import CaptionGenerator

def add_captions_to_video(video, text):
    gen = CaptionGenerator()
    return gen.burn_captions(
        video_path=video, 
        caption_text=text,
        chunk_words=2  # Enable chunking
    )
```

## License

Reusable skill - integrate freely into any project!
