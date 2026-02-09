"""
Demo Framework Orchestrator

Main entry point that runs the complete demo video generation pipeline.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Import framework components
from config_loader import load_config, print_config_summary
from script_generator import generate_voiceover_script, validate_script_timing, print_timing_report
from voiceover_generator import generate_voiceover
from caption_generator import generate_captions, create_styled_ass_file
from video_compositor import composite_final_video, check_ffmpeg_installed
from recording_orchestrator import save_recording_instructions, print_recording_summary

# Load environment variables
load_dotenv()


class PipelineState:
    """Track state of pipeline execution"""
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.script_path = None
        self.voiceover_path = None
        self.srt_path = None
        self.ass_path = None
        self.recording_path = None
        self.bgm_path = None
        self.final_video_path = None
    
    def __repr__(self):
        return f"""Pipeline State:
  Config: {self.config_path}
  Script: {self.script_path or 'Not generated'}
  Voiceover: {self.voiceover_path or 'Not generated'}
  Captions: {self.ass_path or 'Not generated'}
  Recording: {self.recording_path or 'Not provided'}
  Final Video: {self.final_video_path or 'Not created'}
"""


def check_environment() -> dict:
    """
    Check for required API keys and tools
    
    Returns dict of {requirement: status}
    """
    
    checks = {}
    
    # API Keys
    checks['GEMINI_API_KEY'] = bool(os.getenv('GEMINI_API_KEY'))
    checks['OPENAI_API_KEY'] = bool(os.getenv('OPENAI_API_KEY'))
    checks['ELEVENLABS_API_KEY'] = bool(os.getenv('ELEVENLABS_API_KEY'))
    
    # Tools
    checks['FFmpeg'] = check_ffmpeg_installed()
    
    return checks


def print_environment_check(checks: dict):
    """Print status of environment check"""
    
    print("\n" + "="*70)
    print("🔧 ENVIRONMENT CHECK")
    print("="*70)
    
    for requirement, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {requirement}: {'OK' if status else 'MISSING'}")
    
    missing = [k for k, v in checks.items() if not v]
    
    if missing:
        print(f"\n⚠️  Missing requirements: {', '.join(missing)}")
        print("\nRequired API keys should be in .env file:")
        for key in ['GEMINI_API_KEY', 'OPENAI_API_KEY', 'ELEVENLABS_API_KEY']:
            if not checks.get(key):
                print(f"  {key}=your-key-here")
        
        if not checks.get('FFmpeg'):
            print("\nInstall FFmpeg:")
            print("  macOS: brew install ffmpeg")
            print("  Linux: sudo apt install ffmpeg")
    
    print("="*70 + "\n")
    
    return len(missing) == 0


def run_demo_pipeline(
    config_path: str = "../INPUT/configuration/Product_Specs.md",
    recording_path: Optional[str] = None,
    bgm_path: Optional[str] = None,
    skip_script_generation: bool = False,
    skip_voiceover: bool = False,
    skip_captions: bool = False
) -> str:
    """
    Run complete demo video generation pipeline
    
    Args:
        config_path: Path to Product_Specs.md
        recording_path: Optional path to existing screen recording
        bgm_path: Optional path to background music
        skip_script_generation: Skip script generation (use existing)
        skip_voiceover: Skip voiceover generation (use existing)
        skip_captions: Skip caption generation (use existing)
        
    Returns:
        Path to final video file
    """
    
    print("\n" + "="*70)
    print("🎬 DEMO VIDEO PIPELINE - START")
    print("="*70 + "\n")
    
    # Initialize state
    state = PipelineState(config_path)
    
    # Environment check
    env_checks = check_environment()
    if not print_environment_check(env_checks):
        raise RuntimeError("Environment check failed - see missing requirements above")
    
    # Stage 1: Load Configuration
    print("📋 Stage 1: Loading configuration...")
    state.config = load_config(config_path)
    print_config_summary(state.config)
    print()
    
    # Stage 2: Generate Script
    if not skip_script_generation:
        print("✍️  Stage 2: Generating voiceover script with Gemini API...")
        state.script_path = generate_voiceover_script(state.config)
        
        # Validate timing
        timing_results = validate_script_timing(state.script_path, state.config)
        print_timing_report(timing_results)
        
        if timing_results["TOTAL"]["status"] != "✅ OK":
            print("\n⚠️  Script timing validation failed!")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Pipeline halted. Edit script or regenerate.")
                return None
    else:
        state.script_path = "../OUTPUT/scripts/voiceover_script.md"
        print(f"⏭️  Stage 2: Skipping script generation (using {state.script_path})")
    
    # Stage 3: Generate Voiceover
    if not skip_voiceover:
        print("\n🎙️  Stage 3: Generating voiceover with ElevenLabs API...")
        state.voiceover_path = generate_voiceover(state.script_path, state.config)
    else:
        state.voiceover_path = "../OUTPUT/voiceover/voiceover_raw.mp3"
        print(f"⏭️  Stage 3: Skipping voiceover (using {state.voiceover_path})")
    
    # Stage 4: Generate Captions
    if not skip_captions:
        print("\n📝 Stage 4: Generating captions with Whisper API...")
        state.srt_path = generate_captions(state.voiceover_path, state.config)
        state.ass_path = create_styled_ass_file(state.srt_path, state.config)
    else:
        state.ass_path = "../OUTPUT/captions/captions_styled.ass"
        print(f"⏭️  Stage 4: Skipping captions (using {state.ass_path})")
    
    # Stage 5: Recording Instructions
    if not recording_path:
        print("\n📹 Stage 5: Screen Recording Required")
        print("   No recording provided. Generating instructions...")
        save_recording_instructions(state.config)
        print_recording_summary(state.config)
        
        print("\n⚠️  MANUAL STEP REQUIRED:")
        print("   1. Record screen using QuickTime/OBS following instructions")
        print("   2. Save recording as: INPUT/raw_recordings/screen_recording.webm")
        print("   3. Re-run pipeline with: --recording=path/to/recording")
        print()
        print("   OR use browser_subagent for automated recording")
        print()
        
        response = input("Have you completed the recording? Enter path (or 'skip'): ")
        if response.lower() in ['skip', 'n', 'no', '']:
            print("\nPipeline halted at recording stage.")
            print("Intermediate outputs saved:")
            print(f"  Script: {state.script_path}")
            print(f"  Voiceover: {state.voiceover_path}")
            print(f"  Captions: {state.ass_path}")
            return None
        else:
            state.recording_path = response
    else:
        state.recording_path = recording_path
        print(f"📹 Stage 5: Using provided recording: {state.recording_path}")
    
    # Verify recording exists
    if not Path(state.recording_path).exists():
        raise FileNotFoundError(f"Recording not found: {state.recording_path}")
    
    # BGM
    state.bgm_path = bgm_path
    
    # Stage 6: Composite Final Video
    print("\n🎬 Stage 6: Compositing final video with FFmpeg...")
    state.final_video_path = composite_final_video(
        recording_path=state.recording_path,
        voiceover_path=state.voiceover_path,
        captions_path=state.ass_path,
        bgm_path=state.bgm_path,
        config=state.config,
        output_path=f"../OUTPUT/final_video/{state.config.product.name.lower().replace(' ', '_')}_demo_final.mp4"
    )
    
    # Pipeline Complete
    print("\n" + "="*70)
    print("🎉 PIPELINE COMPLETE!")
    print("="*70)
    print(state)
    print("="*70 + "\n")
    
    return state.final_video_path


def resume_from_stage(stage: str, config_path: str = "../INPUT/configuration/Product_Specs.md", **kwargs):
    """
    Resume pipeline from specific stage
    
    Stages:
    - script: Generate script only
    - voiceover: Generate voiceover (assumes script exists)
    - captions: Generate captions (assumes voiceover exists)
    - composite: Composite video (assumes all components exist)
    """
    
    stage_map = {
        'script': {'skip_script_generation': False, 'skip_voiceover': True, 'skip_captions': True},
        'voiceover': {'skip_script_generation': True, 'skip_voiceover': False, 'skip_captions': True},
        'captions': {'skip_script_generation': True, 'skip_voiceover': True, 'skip_captions': False},
        'composite': {'skip_script_generation': True, 'skip_voiceover': True, 'skip_captions': True}
    }
    
    if stage not in stage_map:
        raise ValueError(f"Invalid stage: {stage}. Choose from: {list(stage_map.keys())}")
    
    flags = stage_map[stage]
    flags.update(kwargs)
    
    return run_demo_pipeline(config_path=config_path, **flags)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Demo Video Generation Pipeline")
    parser.add_argument(
        '--config',
        default='../INPUT/configuration/Product_Specs.md',
        help='Path to Product_Specs.md configuration file'
    )
    parser.add_argument(
        '--recording',
        help='Path to screen recording (skip recording stage)'
    )
    parser.add_argument(
        '--bgm',
        help='Path to background music MP3'
    )
    parser.add_argument(
        '--skip-script',
        action='store_true',
        help='Skip script generation (use existing)'
    )
    parser.add_argument(
        '--skip-voiceover',
        action='store_true',
        help='Skip voiceover generation (use existing)'
    )
    parser.add_argument(
        '--skip-captions',
        action='store_true',
        help='Skip caption generation (use existing)'
    )
    parser.add_argument(
        '--resume-from',
        choices=['script', 'voiceover', 'captions', 'composite'],
        help='Resume pipeline from specific stage'
    )
    
    args = parser.parse_args()
    
    try:
        if args.resume_from:
            final_video = resume_from_stage(
                stage=args.resume_from,
                config_path=args.config,
                recording_path=args.recording,
                bgm_path=args.bgm
            )
        else:
            final_video = run_demo_pipeline(
                config_path=args.config,
                recording_path=args.recording,
                bgm_path=args.bgm,
                skip_script_generation=args.skip_script,
                skip_voiceover=args.skip_voiceover,
                skip_captions=args.skip_captions
            )
        
        if final_video:
            print(f"\n✅ SUCCESS! Final video: {final_video}")
            sys.exit(0)
        else:
            print("\n⚠️  Pipeline halted at intermediate stage")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
