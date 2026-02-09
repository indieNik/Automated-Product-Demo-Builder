#!/usr/bin/env python3
"""
Enhanced Voiceover Generator

Generates separate voiceover audio for each scene with:
- Emotional expressions (ElevenLabs v3)
- Scene-specific pacing/tone
- Uses Monika voice (EaBs7G1VibMrNAuz2Na7)
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple

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


class EnhancedVoiceoverGenerator:
    """Generates expressive, scene-specific voiceovers"""
    
    # Monika Voice ID
    VOICE_ID = "EaBs7G1VibMrNAuz2Na7"
    
    # Expression mapping per scene type
    SCENE_EXPRESSIONS = {
        "Hook": ("[concerned]", "[worried]"),
        "Problem": ("[empathetic]", "[serious]"),
        "Solution": ("[excited]", "[optimistic]"),
        "Demo": ("[confident]", "[enthusiastic]"),
        "Results": ("[happy]", "[proud]"),
        "Benefits": ("[excited]", "[delighted]"),
        "CTA": ("[encouraging]", "[warm]"),
        "Tech": ("[excited]", "[proud]")
    }

    def __init__(self, api_key: str):
        self.client = ElevenLabs(api_key=api_key)
    
    def parse_storyline_scripts(self, storyline_path: Path) -> List[dict]:
        """Extract scripts from Storyline.md"""
        content = storyline_path.read_text(encoding='utf-8')
        scenes = []
        
        # Find all scene blocks
        scene_pattern = r'## Scene (\d+): (.+?)\n.*?### Voiceover Script\n(.+?)(?=\n###|\n---|\Z)'
        matches = re.finditer(scene_pattern, content, re.DOTALL)
        
        for match in matches:
            scene_num = int(match.group(1))
            title = match.group(2).strip()
            script = match.group(3).strip()
            
            # Determine scene type for expression
            scene_type = "Demo"  # Default
            if "Hook" in title: scene_type = "Hook"
            elif "Solution" in title: scene_type = "Solution"
            elif "Result" in title: scene_type = "Results"
            elif "CTA" in title: scene_type = "CTA"
            
            scenes.append({
                'scene_number': scene_num,
                'title': title,
                'script': script,
                'type': scene_type
            })
        
        return scenes
    
    def inject_expressions(self, script: str, scene_type: str) -> str:
        """Add expression tags to script start/end"""
        start_expr, end_expr = self.SCENE_EXPRESSIONS.get(scene_type, ("[neutral]", "[neutral]"))
        
        # Don't double add if already present
        if script.startswith("["):
            return script
        
        return f"{start_expr} {script}"

    def generate_scene_audio(
        self, 
        text: str, 
        output_path: Path,
        stability: float = 0.5,
        style: float = 0.5
    ) -> Path:
        """Generate audio for a single scene"""
        
        print(f"🎤 Generating: {output_path.name}")
        print(f"   Text: {text[:50]}...")
        
        try:
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.VOICE_ID,
                text=text,
                model_id="eleven_v3",
                voice_settings=VoiceSettings(
                    stability=stability,
                    similarity_boost=0.75,
                    style=style,
                    use_speaker_boost=True
                )
            )
            
            # Save
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)
            
            print(f"   ✅ Saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
            return None


def main():
    """CLI Entry Point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate enhanced voiceovers")
    parser.add_argument("--storyline", default="../OUTPUT/scripts/Storyline.md")
    parser.add_argument("--output-dir", default="../OUTPUT/voiceover")
    
    args = parser.parse_args()
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found")
        sys.exit(1)
    
    generator = EnhancedVoiceoverGenerator(api_key)
    storyline_path = Path(__file__).parent / args.storyline
    output_dir = Path(__file__).parent / args.output_dir
    
    # 1. Generate Storyline Scenes
    print("🔹 Processing Storyline Scenes...")
    scenes = generator.parse_storyline_scripts(storyline_path)
    
    for scene in scenes:
        script = generator.inject_expressions(scene['script'], scene['type'])
        out_path = output_dir / f"scene_{scene['scene_number']}_vo.mp3"
        
        # Adjust settings based on scene type
        stability = 0.5
        style = 0.5
        if scene['type'] == "Hook":
            style = 0.7  # More dramatic
        elif scene['type'] == "Results":
            style = 0.6  # More excited
            
        generator.generate_scene_audio(script, out_path, stability, style)
    
    # 2. Check for extra generated scenes (Hook/Tech)
    print("\n🔹 Checking for Generated AI Scenes...")
    scenes_dir = output_dir.parent / "scenes"
    
    # Tech Wrap-up script
    try:
        from tech_scanner import TechnologyScanner
        # Locate project root relative to this script
        project_root = Path(__file__).parent.parent.parent
        scanner = TechnologyScanner(project_root)
        tech = scanner.scan_all()
        base_script = scanner.generate_tech_callout_script(tech)
        
        if not base_script:
            print("⚠️  Tech scanner returned empty script. Using fallback.")
            base_script = "Powered by Google Gemini and ElevenLabs."

        tech_script = generator.inject_expressions(base_script, "Tech")
        
        print(f"🎤 Generating Tech VO (Script len: {len(tech_script)})")
        generator.generate_scene_audio(
            tech_script, 
            output_dir / "scene_5_tech_vo.mp3",
            stability=0.5, 
            style=0.8 
        )
    except Exception as e:
        print(f"❌ Failed to generate tech VO: {e}")


if __name__ == "__main__":
    main()
