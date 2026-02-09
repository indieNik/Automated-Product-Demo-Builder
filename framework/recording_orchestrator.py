"""
Recording Orchestrator

Automates browser walkthrough for screen recording using browser_subagent.
Generates detailed task prompts from Product_Specs.md demo scenes.
"""

from pathlib import Path
from typing import List
from config_loader import load_config, DemoConfig, DemoScene


def generate_browser_task_for_scene(scene: DemoScene, product_url: str) -> str:
    """
    Convert scene configuration into browser_subagent task prompt
    
    Args:
        scene: DemoScene with actions and visuals
        product_url: Base URL of the product
        
    Returns:
        Detailed task prompt for browser automation
    """
    
    task_lines = [
        f"# Scene: {scene.name}",
        f"Duration: {scene.duration} ({scene.duration_seconds} seconds)",
        f"Objective: {scene.objective}",
        "",
        "## Actions:"
    ]
    
    for action in scene.actions:
        task_lines.append(f"- {action}")
    
    task_lines.extend([
        "",
        "## Important:",
        f"- Allow {scene.duration_seconds} seconds for this scene",
        "- Move mouse slowly and deliberately",
        "- Pause 2-3 seconds after each major action to allow visibility",
        "- Ensure all UI elements are clearly visible before interacting",
        ""
    ])
    
    return "\n".join(task_lines)


def generate_full_recording_task(config: DemoConfig) -> str:
    """
    Generate complete browser automation task from all demo scenes
    
    This creates a single comprehensive prompt that walks through
    the entire demo from start to finish.
    
    Args:
        config: DemoConfig with product URL and scenes
        
    Returns:
        Full recording task prompt
    """
    
    # Filter scenes that require browser interaction
    interactive_scenes = [
        scene for scene in config.demo.scenes
        if scene.actions and len(scene.actions) > 0
    ]
    
    if not interactive_scenes:
        raise ValueError("No interactive scenes found in Product_Specs.md")
    
    task_lines = [
        f"# Product Demo Recording: {config.product.name}",
        "",
        f"Record a complete walkthrough of {config.product.name} demonstrating",
        "the key features and functionality as outlined in the scenes below.",
        "",
        "## Recording Requirements:",
        "- Screen resolution: 1920x1080",
        "- Clear browser window (no bookmarks bar, no distracting tabs)",
        "- Smooth mouse movements",
        "- Deliberate pacing (2-3 seconds between actions)",
        f"- Total duration: ~{sum(s.duration_seconds for s in interactive_scenes)} seconds for interactive portions",
        "",
        f"## Starting Point:",
        f"Navigate to: {config.product.url}",
        "",
        "---",
        ""
    ]
    
    # Add each scene
    for i, scene in enumerate(interactive_scenes, 1):
        scene_task = generate_browser_task_for_scene(scene, config.product.url)
        task_lines.append(f"## Step {i}: {scene.name}")
        task_lines.append(scene_task)
        task_lines.append("---")
        task_lines.append("")
    
    # Add completion instruction
    task_lines.extend([
        "## Completion:",
        "Once all scenes are complete, return to this conversation with:",
        "- Confirmation that recording is saved",
        "- Path to the recorded file (.webm format)",
        "- Any issues encountered during recording",
        ""
    ])
    
    return "\n".join(task_lines)


def save_recording_instructions(config: DemoConfig, output_path: str = "../INPUT/raw_recordings/RECORDING_INSTRUCTIONS.md") -> str:
    """
    Save browser recording instructions to file for manual reference
    
    Useful if browser_subagent fails or user prefers manual recording
    """
    
    instructions = generate_full_recording_task(config)
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(instructions, encoding='utf-8')
    
    print(f"✅ Recording instructions saved!")
    print(f"   {output_file}")
    print()
    print("   Use these instructions for:")
    print("   1. Manual screen recording (QuickTime, OBS)")
    print("   2. Reference for browser_subagent automation")
    print()
    
    return str(output_file)


def print_recording_summary(config: DemoConfig):
    """Print summary of what needs to be recorded"""
    
    interactive_scenes = [s for s in config.demo.scenes if s.actions]
    
    print("="*70)
    print("📹 RECORDING PLAN")
    print("="*70)
    print(f"\nProduct: {config.product.name}")
    print(f"URL: {config.product.url}")
    print(f"\nTotal Scenes: {len(config.demo.scenes)}")
    print(f"Interactive Scenes: {len(interactive_scenes)}")
    print(f"Total Duration: {config.demo.duration_seconds}s target")
    
    print(f"\n{'Scene':<30} {'Duration':<15} {'Actions'}")
    print("-"*70)
    
    for scene in interactive_scenes:
        print(f"{scene.name[:28]:<30} {scene.duration:<15} {len(scene.actions)} steps")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else "../INPUT/configuration/Product_Specs.md"
    
    try:
        config = load_config(config_path)
        
        # Print summary
        print_recording_summary(config)
        
        # Generate instructions
        instructions_path = save_recording_instructions(config)
        
        # Generate full task
        task = generate_full_recording_task(config)
        
        print("\n📋 BROWSER AUTOMATION TASK:")
        print("-"*70)
        print(task)
        
        print("\n💡 USAGE:")
        print("   Option 1 (Automated): Use browser_subagent tool with the task above")
        print("   Option 2 (Manual): Use QuickTime/OBS and follow RECORDING_INSTRUCTIONS.md")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
