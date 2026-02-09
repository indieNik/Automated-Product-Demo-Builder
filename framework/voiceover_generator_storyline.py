#!/usr/bin/env python3
"""
Unified Voiceover Generator (Storyline-Driven)

Generates voiceover from Storyline.md instead of separate script file.

Workflow:
1. Parse Storyline.md to extract voiceover scripts from each scene
2. Concatenate scripts with 1-second silence between scenes
3. Generate voiceover using ElevenLabs v3 (expression support)
4. Export as MP3

This replaces the old script_generator.py → voiceover_generator.py flow.
Now: Storyline.md → voiceover directly.
"""

import os
import sys
import re
from pathlib import Path
from typing import List
import io

# ElevenLabs SDK
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
except ImportError:
    print("⚠️  ElevenLabs SDK not installed. Install with: pip install elevenlabs")
    sys.exit(1)

# Add parent to path for config_loader
sys.path.insert(0, str(Path(__file__).parent))
from config_loader import load_config, DemoConfig


def parse_storyline_scripts(storyline_path: Path) -> List[dict]:
    """
    Extract voiceover scripts from Storyline.md
    
    Returns:
        List of dicts with {scene_number, title, script}
    """
    content = storyline_path.read_text(encoding='utf-8')
    scenes = []
    
    # Find all scene blocks
    scene_pattern = r'## Scene (\d+): (.+?)\n.*?### Voiceover Script\n(.+?)(?=\n###|\n---|\Z)'
    matches = re.finditer(scene_pattern, content, re.DOTALL)
    
    for match in matches:
        scene_num = int(match.group(1))
        title = match.group(2).strip()
        script = match.group(3).strip()
        
        scenes.append({
            'scene_number': scene_num,
            'title': title,
            'script': script
        })
    
    return scenes


def generate_voiceover_from_storyline(
    storyline_path: Path,
    config: DemoConfig,
    output_path: Path,
    add_scene_markers: bool = False
) -> str:
    """
    Generate voiceover from storyline scenes
    
    Args:
        storyline_path: Path to Storyline.md
        config: DemoConfig with voiceover settings
        output_path: Where to save the MP3
        add_scene_markers: If True, add silence between scenes
        
    Returns:
        Path to generated audio file
    """
    print("="*80)
    print("🎙️  UNIFIED VOICEOVER GENERATION")
    print("="*80)
    print(f"Source: {storyline_path}")
    print(f"Output: {output_path}")
    print()
    
    # Parse scenes
    print("📖 Parsing storyline...")
    scenes = parse_storyline_scripts(storyline_path)
    print(f"✅ Found {len(scenes)} scenes with scripts")
    print()
    
    # Concatenate scripts
    full_script = ""
    for i, scene in enumerate(scenes):
        print(f"Scene {scene['scene_number']}: {scene['title']}")
        print(f"   Script length: {len(scene['script'])} chars")
        
        full_script += scene['script']
        
        # Add pause between scenes (except last)
        if add_scene_markers and i < len(scenes) - 1:
            full_script += " ... "  # ElevenLabs will naturally pause here
    
    print()
    print(f"📊 Total script length: {len(full_script)} chars")
    print(f"   Estimated duration: {len(full_script.split()) / config.voiceover.pacing_wpm:.1f} min")
    print()
    
    # Initialize ElevenLabs
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
    
    client = ElevenLabs(api_key=api_key)
    
    # Generate voiceover
    print(f"🎤 Generating with ElevenLabs...")
    print(f"   Voice: {config.voiceover.voice_id}")
    print(f"   Model: eleven_v3 (v3 with expression)")
    print(f"   Stability: {config.voiceover.stability}")
    print()
    
    try:
        audio_generator = client.text_to_speech.convert(
            voice_id=config.voiceover.voice_id,
            text=full_script,
            model_id="eleven_v3",  # v3 model with expression support
            voice_settings=VoiceSettings(
                stability=config.voiceover.stability,
                similarity_boost=config.voiceover.clarity,
                style=config.voiceover.style,
                use_speaker_boost=True
            )
        )
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Collect audio bytes
        audio_bytes = b"".join(audio_generator)
        
        # Write to file
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        
        print(f"✅ Voiceover generated!")
        print(f"   Saved to: {output_path}")
        print(f"   File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        print()
        
        return str(output_path)
        
    except Exception as e:
        print(f"❌ ElevenLabs generation failed: {e}")
        raise


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate voiceover from storyline")
    parser.add_argument(
        "--storyline",
        default="../OUTPUT/scripts/Storyline.md",
        help="Path to Storyline.md"
    )
    parser.add_argument(
        "--config",
        default="../INPUT/configuration/Product_Specs.md",
        help="Path to Product_Specs.md (for voiceover settings)"
    )
    parser.add_argument(
        "--output",
        default="../OUTPUT/voiceover/voiceover_storyline.mp3",
        help="Output path for voiceover MP3"
    )
    parser.add_argument(
        "--scene-markers",
        action="store_true",
        help="Add silence between scenes"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    storyline_path = Path(__file__).parent / args.storyline
    config_path = Path(__file__).parent / args.config
    output_path = Path(__file__).parent / args.output
    
    if not storyline_path.exists():
        print(f"❌ Storyline not found: {storyline_path}")
        sys.exit(1)
    
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        sys.exit(1)
    
    # Load config
    print(f"📄 Loading config from: {config_path}")
    config = load_config(str(config_path))
    print()
    
    # Generate voiceover
    audio_path = generate_voiceover_from_storyline(
        storyline_path,
        config,
        output_path,
        add_scene_markers=args.scene_markers
    )
    
    print("="*80)
    print("✅ VOICEOVER GENERATION COMPLETE")
    print("="*80)
    print()
    print("🎯 Next steps:")
    print("   1. Review voiceover: open", audio_path)
    print("   2. Generate captions: python3 caption_generator.py --storyline")
    print("   3. Compose video: python3 smart_compositor.py")
    print()


if __name__ == "__main__":
    main()
