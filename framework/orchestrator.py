#!/usr/bin/env python3
"""
Master Orchestrator - Autonomous Product Demo Generator (Professional Edition)

Single-command execution: Product_Specs.md → Professional AI Demo Video

Workflow:
1. Phase 1: Generate Storyline (Storyline Intelligence)
2. Phase 2: Record browser scenes (Autonomous Agent)
3. Phase 3: Generate AI Scenes (Hook + Tech Wrap-up with Gemini)
4. Phase 4: Generate Enhanced Voiceover (Monika + Emotional Expressions)
5. Phase 5: Smart Composition (Stitch professional demo)

Usage: python3 orchestrator.py [--config Product_Specs.md]
"""

import os
import sys
import shutil
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Logging
def setup_logging(log_file_path):
    """Configure logging to both file and console"""
    # Create logger
    logger = logging.getLogger('Orchestrator')
    logger.setLevel(logging.DEBUG)

    # Create file handler which logs even debug messages
    fh = logging.FileHandler(log_file_path)
    fh.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def run_phase(phase_num: int, phase_name: str, command: list, cwd: Path, logger: logging.Logger) -> bool:
    """Execute a phase and track success"""
    logger.info("="*80)
    logger.info(f"🎬 PHASE {phase_num}: {phase_name.upper()}")
    logger.info("="*80)
    logger.info(f"Command: {' '.join(command)}")
    
    try:
        # Run command and capture output
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Stream output to log
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.debug(output.strip())
                print(output.strip()) # Also print to stdout for real-time feedback

        # Check for errors
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info(f"✅ Phase {phase_num} complete: {phase_name}")
            return True
        else:
            logger.error(f"❌ Phase {phase_num} failed: {phase_name}")
            logger.error(f"Error Output: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Phase {phase_num} failed: {phase_name}")
        logger.error(f"Error: {e}")
        return False

def get_product_name(config_path: Path):
    """Extract product name from config file or filename"""
    try:
        with open(config_path, 'r') as f:
            for line in f:
                if "Product Name:" in line:
                    return line.split(":", 1)[1].strip().replace(" ", "")
    except Exception:
        pass
    # Fallback to config filename without extension
    return config_path.stem

def main():
    """Main orchestration"""
    
    parser = argparse.ArgumentParser(
        description="Autonomous Product Demo Generator - Full Pipeline"
    )
    parser.add_argument(
        "--config",
        default="../INPUT/configuration/Product_Specs.md",
        help="Path to Product_Specs.md"
    )
    parser.add_argument(
        "--skip-recording",
        action="store_true",
        help="Skip browser recording (use existing)"
    )
    parser.add_argument(
        "--analyze-url",
        help="Analyze a product URL to auto-generate Product_Specs.md"
    )
    parser.add_argument(
        "--product-name",
        help="Product Name (optional, used with --analyze-url)"
    )
    parser.add_argument(
        "--credentials",
        help="Credentials in format username/password (optional)"
    )
    
    args = parser.parse_args()
    
    # Determine absolute paths
    framework_dir = Path(__file__).parent.resolve()
    base_dir = framework_dir.parent.resolve() # Root of the project

    # Resolve    # If config not provided, try to find it in product folders
    if not args.config and args.product_name:
        potential_path = base_dir / args.product_name / "INPUT" / "configuration" / "Product_Specs.md"
        if potential_path.exists():
            args.config = str(potential_path)
            
    # Default to generic if still not found (legacy)
    if not args.config:
        args.config = "../INPUT/configuration/Product_Specs.md"
        
    abs_config_path = Path(args.config).resolve()
    if not abs_config_path.is_absolute():
        abs_config_path = (framework_dir / args.config).resolve()
    else:
        abs_config_path = Path(args.config).resolve()

    # Determine Product Name
    product_name = args.product_name if args.product_name else get_product_name(abs_config_path)
    if not product_name:
        product_name = "GenericProduct"

    # Create Product Directories
    product_dir = base_dir / product_name
    input_base_dir = product_dir / "INPUT"
    input_config_dir = input_base_dir / "configuration"
    input_recordings_dir = input_base_dir / "raw_recordings"
    input_assets_dir = input_base_dir / "assets"
    
    # Ensure they exist
    input_config_dir.mkdir(parents=True, exist_ok=True)
    input_recordings_dir.mkdir(parents=True, exist_ok=True)
    input_assets_dir.mkdir(parents=True, exist_ok=True)

    # Dynamic Timestamped Output & Input History
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_dir = product_dir / f"OUTPUT-{timestamp}"
    input_history_dir = product_dir / f"INPUT-{timestamp}"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    input_history_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup subdirectories in OUTPUT
    (output_dir / "scripts").mkdir(exist_ok=True)
    (output_dir / "scenes").mkdir(exist_ok=True)
    (output_dir / "voiceover").mkdir(exist_ok=True)
    (output_dir / "final_video").mkdir(exist_ok=True)
    
    # Archive Input Config
    if abs_config_path.exists():
         shutil.copy(abs_config_path, input_history_dir / "Product_Specs.md")
         # Also ensure it's in the main INPUT/configuration if different
         if abs_config_path.parent != input_config_dir:
             shutil.copy(abs_config_path, input_config_dir / "Product_Specs.md")

    # Setup Logging
    log_file = product_dir / f"run_{product_name}.log"
    logger = setup_logging(log_file)

    logger.info("="*80)
    logger.info("🚀 AUTONOMOUS PRODUCT DEMO GENERATOR (PRO EDITION)")
    logger.info("="*80)
    logger.info(f"Config: {abs_config_path}")
    logger.info(f"Product: {product_name}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Input Archive: {input_history_dir}")
    logger.info(f"Started: {timestamp}")
    
    # Track phases
    phases_completed = []
    start_time = datetime.now()

    # Phase 0: Product Analysis (Optional)
    if args.analyze_url:
        analyze_cmd = [
            "python3",
            "product_analyzer.py",
            f"--url={args.analyze_url}",
            f"--output={abs_config_path}"
        ]
        if args.product_name:
            analyze_cmd.append(f"--name={args.product_name}")
        if args.credentials:
            analyze_cmd.append(f"--credentials={args.credentials}")
            
        if not run_phase(
            0,
            "Product Analysis & Spec Generation",
            analyze_cmd,
            framework_dir,
            logger
        ):
            logger.error("Product Analysis failed")
            sys.exit(1)
        phases_completed.append("Product Analysis")
    
        # Re-copy the generated config to history
        if abs_config_path.exists():
             shutil.copy(abs_config_path, input_history_dir / "Product_Specs.md")

    # Phase 1: Browser Recording & Video Generation (Record First)
    if not args.skip_recording:
        # Save recordings to the timestamped INPUT archive for this run
        recording_output_dir = input_history_dir / "raw_recordings"
        recording_output_dir.mkdir(exist_ok=True)

        if not run_phase(
            1,
            "Autonomous Video Recording",
            [
                "python3",
                "browser_recorder.py",
                f"--storyline={output_dir}/scripts/Storyline.md", 
                f"--config={abs_config_path}",
                f"--output-dir={recording_output_dir}" 
            ],
            framework_dir,
            logger
        ):
            logger.error("Recording failed. Pipeline stopped.")
            logger.error("Recording failed. Pipeline stopped.")
            sys.exit(1)
        phases_completed.append("Autonomous Video Recording")
    else:
        logger.info("Skipping Phase 1: Browser Recording (User Request)")
        # If skipping, we expect assets to be in the staging INPUT/raw_recordings or manually placed
        # We should check if we need to copy them to the input_history_dir for this run
        # For now, let's assume the compositor will look in the input_history_dir, so we might need to populate it?
        # Actually, let's keep it simple: If skipped, we assume the user might have provided a specific recording input
        # OR we just explicitly copy the staging recordings to the history dir if they exist
        staging_recs = input_recordings_dir
        if staging_recs.exists():
             shutil.copytree(staging_recs, input_history_dir / "raw_recordings", dirs_exist_ok=True)

    # Phase 2: Storyline Generation (Context-Aware)
    if not run_phase(
        2,
        "Storyline Intelligence Engine",
        [
            "python3",
            "storyline_generator.py",
            f"--config={abs_config_path}",
            f"--output={output_dir}/scripts/Storyline.md"
        ],
        framework_dir,
        logger
    ):
        logger.error("Pipeline failed at Phase 2")
        sys.exit(1)
    phases_completed.append("Storyline Generation")
        
    # Phase 3: AI Scene Generation (Hooks/B-Roll)
    if not run_phase(
        3,
        "Generative Visuals Engine (Hook)",
        [
            "python3",
            "scene_generator.py",
            "--type=hook",
            f"--output-dir={output_dir}/scenes"
        ],
        framework_dir,
        logger
    ):
        logger.error("Pipeline failed at Phase 3 (Hook Scene)")
        sys.exit(1)
    
    # Tech Stack Scene
    if not run_phase(
        3,
        "Generative Visuals Engine (Tech Stack)",
        [
            "python3",
            "scene_generator.py",
            "--type=tech",
             f"--output-dir={output_dir}/scenes"
        ],
        framework_dir,
        logger
    ):
        logger.error("Pipeline failed at Phase 3 (Tech Stack Scene)")
        sys.exit(1)
    phases_completed.append("AI Scene Generation")
        
    # Phase 4: Enhanced Voiceover Generation
    if not run_phase(
        4,
        "Neural Voice Synthesis",
        [
            "python3",
            "voiceover_generator.py",
            f"--storyline={output_dir}/scripts/Storyline.md",
            f"--output_dir={output_dir}/voiceover"
        ],
        framework_dir,
        logger
    ):
        logger.error("Pipeline failed at Phase 4")
        sys.exit(1)
    phases_completed.append("Enhanced Voiceover")

    # Phase 6: Professional Video Composition
    if not run_phase(
        6,
        "Professional Smart Composition",
        [
            "python3",
            "smart_compositor_v2.py",
            f"--storyline={output_dir}/scripts/Storyline.md", 
            f"--output={output_dir}/final_video/Final_Demo_Video.mp4",
            f"--recordings-dir={input_history_dir}/raw_recordings",
            f"--scenes-dir={output_dir}/scenes",
            f"--voiceover-dir={output_dir}/voiceover",
            "--captions=true"
        ],
        framework_dir,
        logger
    ):
        logger.error("Pipeline failed at Phase 6")
        sys.exit(1)
    phases_completed.append("Video Composition")
    
    # Summary
    elapsed = datetime.now() - start_time
    
    logger.info("="*80)
    logger.info("🎉 PIPELINE EXECUTION SUMMARY")
    logger.info("="*80)
    logger.info(f"Total time: {elapsed.total_seconds():.1f} seconds")
    logger.info("Phases completed:")
    for i, phase in enumerate(phases_completed, 1):
        logger.info(f"  {i}. {phase}")
    logger.info("📁 Generated Assets:")
    logger.info(f"  - Storyline: {output_dir}/scripts/Storyline.md")
    logger.info(f"  - Recordings: {input_history_dir}/raw_recordings/")
    logger.info(f"  - AI Scenes: {output_dir}/scenes/")
    logger.info(f"  - Voiceovers: {output_dir}/voiceover/")
    logger.info(f"  - FINAL VIDEO: {output_dir}/final_video/Final_Demo_Video.mp4")
    logger.info(f"  - LOG FILE: {log_file}")

if __name__ == "__main__":
    main()
