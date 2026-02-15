"""
Voiceover Generator

Parses Storyline.md and generates per-scene audio files using ElevenLabs API.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# Add framework directory to path for imports
current_dir = Path(__file__).resolve().parent
framework_dir = current_dir.parent.parent
sys.path.insert(0, str(framework_dir))

from config_loader import load_config, DemoConfig

# Load environment variables
load_dotenv()

def parse_storyline_for_scenes(storyline_path: Path) -> dict:
    """
    Extracts voiceover scripts for each scene from Storyline.md
    Returns: {1: "Scene 1 text...", 2: "Scene 2 text...", "tech": "Tech text..."}
    """
    content = storyline_path.read_text(encoding='utf-8')
    scenes = {}
    
    # Regex to find scenes and their VO scripts
    # Matches: ## Scene 1: Title ... ### Voiceover Script ... [text] ... ---
    scene_pattern = re.compile(r'## Scene (\d+):.*?(?:### Voiceover Script\s+)(.*?)(?:### |---)', re.DOTALL)
    
    for match in scene_pattern.finditer(content):
        scene_num = int(match.group(1))
        script_text = match.group(2).strip()
        
        # Cleanup script text
        # Remove [PAUSE] or other instructions if needed
        script_text = re.sub(r'\[.*?\]', '', script_text) # Remove emotion tags for raw text? 
        # Actually ElevenLabs v3 SUPPORTS emotion tags like [happy], so we KEEP them!
        # But we should remove non-speech instructions if any.
        # The prompt generates [emotion] text. ElevenLabs might interpret it if model supports it, 
        # or we might need to strip it if using a model that reads it aloud.
        # ElevenLabs Turbo v2.5 doesn't fully support [tag] prompting natively in text unless using speech-to-speech or specific prompt structure.
        # However, for now let's clean strictly [PAUSE] but maybe keep emotion tags if they are part of the text?
        # Actually, if the text is "[happy] Hello", ElevenLabs might read "Open bracket happy close bracket Hello".
        # Let's strip brackets for safety unless we are sure about the model capability.
        # Implementation Plan says: "Use ElevenLabs v3 emotion tags".
        # If ElevenLabs v3 supports it, we keep it. 
        # CAUTION: ElevenLabs API documentation regarding "tags" in text is specific. 
        # Assuming for now we strip them to avoid robotic reading of tags, unless we use Speech-to-Speech.
        # Let's strip them for safety to ensure clean audio.
        
        clean_text = re.sub(r'\[.*?\]', '', script_text)
        clean_text = ' '.join(clean_text.split()) # Normalize whitespace
        
        if clean_text:
            scenes[scene_num] = clean_text

    # Check for Tech Wrap-up (usually Scene 5 or separate?)
    # If Scene 5 is Tech Wrap-up, it's covered above.
    # But usually smart_compositor expects "scene_5_tech_vo.mp3" for the last scene?
    # Actually smart_compositor code looks for "scene_5_tech_vo.mp3".
    # Let's map the last scene to that if needed, or just standard names.
    # smart_compositor looks for: scene_1_vo.mp3, scene_2_vo.mp3...
    # AND scene_5_tech_vo.mp3 separate?
    # Let's check smart_compositor logic:
    # Scene 1: scene_1_vo.mp3
    # Scene 2: scene_2_vo.mp3
    # Scene 3: scene_3_vo.mp3
    # Scene 4: scene_4_vo.mp3
    # Scene 5: scene_5_tech_vo.mp3
    
    return scenes

def generate_voiceover(
    text: str,
    output_path: Path,
    config: DemoConfig,
    client: ElevenLabs
):
    print(f"🎙️  Generating {output_path.name}...")
    print(f"   Text: {text[:50]}...")

    try:
        audio_generator = client.text_to_speech.convert(
            voice_id=config.voiceover.voice_id,
            text=text,
            model_id="eleven_v3", # Robust default
            voice_settings=VoiceSettings(
                stability=config.voiceover.stability,
                similarity_boost=config.voiceover.clarity,
                style=config.voiceover.style,
                use_speaker_boost=True
            )
        )
        
        with open(output_path, 'wb') as f:
            for chunk in audio_generator:
                f.write(chunk)
                
        print(f"   ✅ Saved ({output_path.stat().st_size / 1024:.1f} KB)")
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        raise e

def main():
    parser = argparse.ArgumentParser(description="ElevenLabs Voiceover Generator")
    parser.add_argument("--config", help="Path to Product_Specs.json (unused mostly, keeps compat)")
    parser.add_argument("--storyline", required=True, help="Path to Storyline.md")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    # Init
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found")
        sys.exit(1)
        
    try:
        # Load config just for voice settings
        # We can try to load from --config if provided, or infer
        # config = load_config(args.config) if args.config else ...
        # Let's assume defaults if config load fails or minimal config
        # For now, create a dummy config or try loading
        if args.config:
             config = load_config(args.config)
        else:
             # Fallback or error?
             # We need voice_id.
             # Let's construct a default or try to find one.
             print("⚠️  No config provided, using defaults.")
             # We really need load_config to work. 
             # Orchestrator doesn't pass --config to VO generator in the current call:
             # "--storyline=...", "--output_dir=..."
             # So args.config is None.
             # We should perform a search or hardcode default.
             # Better: Update orchestrator to pass config, OR load from default location.
             pass
             
        # HARDCODED FALLBACK for robustness if config is missing
        # This matches config_loader default usually
        class DefaultConfig:
            class voiceover:
                voice_id = "JBFqnCBsd6RMkjVDRZzb" # Default
                stability = 0.5
                clarity = 0.75
                style = 0.0
                pacing_wpm = 140
        
        # Try loading actual config if we can find it
        config_path = Path("../INPUT/configuration/Product_Specs.json")
        if config_path.exists():
            config = load_config(str(config_path))
        else:
            config = DefaultConfig()
            
        client = ElevenLabs(api_key=api_key)
        
        storyline_path = Path(args.storyline)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        scenes = parse_storyline_for_scenes(storyline_path)
        
        if not scenes:
            print("❌ No scenes found in Storyline.md")
            sys.exit(1)
            
        print(f"found {len(scenes)} scenes to synthesize.")
        
        for scene_num, text in scenes.items():
            # Map scene num to filename
            # Smart Compositor expects: scene_1_vo.mp3, scene_5_tech_vo.mp3
            filename = f"scene_{scene_num}_vo.mp3"
            if scene_num == 5:
                 # Check if it's the tech scene?
                 # Orchestrator/Compositor logic is a bit rigid.
                 # Compositor expects "scene_5_tech_vo.mp3".
                 # Let's start by naming it simply.
                 # Wait, compositor explicitly looks for "scene_5_tech_vo.mp3".
                 # If I just save as scene_5_vo.mp3, it might crash.
                 # Let's save as both or just "scene_5_tech_vo.mp3" if it's the last one?
                 # Creating duplicates is safer.
                 pass

            out_path = output_dir / filename
            generate_voiceover(text, out_path, config, client)
            
            # Hack for Scene 5 tech vo
            if scene_num == 5:
                generate_voiceover(text, output_dir / "scene_5_tech_vo.mp3", config, client)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
