"""
Voiceover Generator

Converts script to audio using ElevenLabs API.
"""

import os
from pathlib import Path
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

from config_loader import load_config, DemoConfig

# Load environment variables
load_dotenv()


def generate_voiceover(
    script_path: str,
    config: DemoConfig,
    output_path: str = "../OUTPUT/voiceover/voiceover_raw.mp3"
) -> str:
    """
    Generate voiceover audio from script using ElevenLabs API
    
    Args:
        script_path: Path to voiceover script markdown file
        config: DemoConfig with voiceover settings
        output_path: Where to save generated audio
        
    Returns:
        Path to generated MP3 file
    """
    
    # Get API key
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
    
    # Read script
    script_content = Path(script_path).read_text(encoding='utf-8')
    
    # Extract only narration (remove markdown headers and metadata)
    import re
    
    # Remove front matter
    script_content = re.sub(r'^#.*?\n---\n', '', script_content, flags=re.DOTALL)
    
    # Remove scene headers and production notes
    script_content = re.sub(r'##\s+Scene\s+\d+:.*?\n', '', script_content)
    script_content = re.sub(r'\*\*Duration Target:.*?\*\*', '', script_content)
    script_content = re.sub(r'---\n##\s+Production Notes.*', '', script_content, flags=re.DOTALL)
    
    # Remove [PAUSE] markers (will be handled in post-production)
    script_content = re.sub(r'\[PAUSE\]', '', script_content)
    
    # Remove markdown bold formatting
    script_content = re.sub(r'\*\*(.*?)\*\*', r'\1', script_content)
    
    # Clean up extra whitespace
    script_content = '\n'.join([line.strip() for line in script_content.split('\n') if line.strip()])
    
    print("🎙️  Generating voiceover with ElevenLabs...")
    print(f"   Voice: {config.voiceover.voice_id}")
    print(f"   Script length: {len(script_content.split())} words")
    print(f"   Estimated duration: {len(script_content.split()) / config.voiceover.pacing_wpm:.1f} minutes")
    print()
    
    # Initialize ElevenLabs client
    client = ElevenLabs(api_key=api_key)
    
    # Generate audio
    audio_generator = client.text_to_speech.convert(
        voice_id=config.voiceover.voice_id,
        text=script_content,
        model_id="eleven_v3",  # V3 model with expression support ([excited], [sad], etc.)
        voice_settings=VoiceSettings(
            stability=config.voiceover.stability,
            similarity_boost=config.voiceover.clarity,
            style=config.voiceover.style,
            use_speaker_boost=True
        )
    )
    
    # Save to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write audio chunks
    with open(output_file, 'wb') as f:
        for chunk in audio_generator:
            f.write(chunk)
    
    print(f"✅ Voiceover generated successfully!")
    print(f"   Saved to: {output_file}")
    print(f"   File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    
    return str(output_file)


if __name__ == "__main__":
    import sys
    
    # Usage: python voiceover_generator.py [config_path] [script_path]
    config_path = sys.argv[1] if len(sys.argv) > 1 else "../INPUT/configuration/Product_Specs.md"
    script_path = sys.argv[2] if len(sys.argv) > 2 else "../OUTPUT/scripts/voiceover_script.md"
    
    try:
        config = load_config(config_path)
        audio_path = generate_voiceover(script_path, config)
        
        print("✅ Ready for caption generation!")
        print(f"   Next: python caption_generator.py {audio_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
