#!/usr/bin/env python3
"""
Autonomous Browser Recording System

Parses Storyline.md and executes browser actions to record product demo footage.

Workflow:
1. Parse Storyline.md to extract scenes + browser actions
2. For each scene with browser actions:
   - Execute actions via browser_subagent
   - Capture recording (WebP format)
   - Save to 01_raw_recordings/scene_[N].webp
3. Handle errors with fallbacks (screenshots, retries)
4. Generate manifest of recorded scenes

This eliminates manual recording - fully autonomous from storyline to footage.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import threading
import shutil
import subprocess

@dataclass
class SceneRecording:
    """Recording configuration for a single scene"""
    scene_number: int
    title: str
    duration_seconds: int
    browser_actions: List[str]
    has_actions: bool
    recording_path: Optional[Path] = None
    status: str = "pending"  # pending, recording, success, failed, skipped
    error_message: Optional[str] = None


class StorylineParser:
    """Parses Storyline.md into structured scene data"""
    
    def __init__(self, storyline_path: Path):
        self.storyline_path = storyline_path
        self.content = storyline_path.read_text(encoding='utf-8')
    
    def parse_scenes(self) -> List[SceneRecording]:
        """Extract all scenes with browser actions from storyline"""
        scenes = []
        
        # Find all scene blocks
        # Support both Storyline.md (## Scene 1) and Product_Specs.md (### Scene 1)
        # Specs format: ### Scene 1: Title (0:00-0:30)
        
        # Regex for Product_Specs.md style
        specs_pattern = r'### Scene (\d+): (.+?) \((\d+):(\d+)-(\d+):(\d+)\)'
        specs_matches = list(re.finditer(specs_pattern, self.content))
        
        if specs_matches:
             for match in specs_matches:
                scene_num = int(match.group(1))
                title = match.group(2).strip()
                # Calculate duration from timestamps
                start_min, start_sec = int(match.group(3)), int(match.group(4))
                end_min, end_sec = int(match.group(5)), int(match.group(6))
                start_seconds = start_min * 60 + start_sec
                end_seconds = end_min * 60 + end_sec
                duration = end_seconds - start_seconds
                
                # Extract block
                scene_start = match.end()
                next_scene = re.search(r'\n### Scene \d+:', self.content[scene_start:])
                scene_end = scene_start + next_scene.start() if next_scene else len(self.content)
                scene_block = self.content[scene_start:scene_end]
                
                self._parse_block(scenes, scene_num, title, duration, scene_block)
                
        else:
            # Fallback to Storyline.md style
            scene_pattern = r'## Scene (\d+): (.+?)\n\*\*Duration\*\*: (\d+)s'
            scene_matches = re.finditer(scene_pattern, self.content)
            
            for match in scene_matches:
                scene_num = int(match.group(1))
                title = match.group(2).strip()
                duration = int(match.group(3))
                
                # Extract block
                scene_start = match.end()
                next_scene = re.search(r'\n## Scene \d+:', self.content[scene_start:])
                scene_end = scene_start + next_scene.start() if next_scene else len(self.content)
                scene_block = self.content[scene_start:scene_end]
                
                self._parse_block(scenes, scene_num, title, duration, scene_block)
        
        return scenes

    def _parse_block(self, scenes, scene_num, title, duration, scene_block):
        """Helper to parse actions from a scene block"""
            
        # Parse browser actions
        # Try '### Browser Actions' (Storyline.md) OR '**Actions:**' (Product_Specs.md)
        actions_matches = []
        
        # Check for ### Browser Actions section
        actions_section = re.search(
            r'### Browser Actions\n(.*?)(?=\n###|\n---|\Z)',
            scene_block,
            re.DOTALL
        )
        if actions_section:
            actions_matches = re.findall(r'^- (.+)$', actions_section.group(1), re.MULTILINE)
        else:
            # Check for **Actions:** section
            actions_section = re.search(
                r'\*\*Actions:\*\*\n(.*?)(?=\n###|\n\*\*|\n---|\Z)',
                scene_block,
                re.DOTALL
            )
            if actions_section:
                actions_matches = re.findall(r'^- (.+)$', actions_section.group(1), re.MULTILINE)
        
        browser_actions = [a.strip() for a in actions_matches if a.strip()]
        has_actions = bool(browser_actions)
        
        scene = SceneRecording(
            scene_number=scene_num,
            title=title,
            duration_seconds=duration,
            browser_actions=browser_actions,
            has_actions=has_actions
        )
        scenes.append(scene)
        
        return scenes


class BrowserRecorder:
    """Executes browser actions and captures recordings"""
    
    def __init__(self, output_dir: Path, config=None):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config
    
    def convert_actions_to_instructions(self, actions: List[str], scene_title: str, duration: int) -> str:
        """
        Convert storyline actions into detailed browser automation instructions
        
        Args:
            actions: List of browser actions from storyline
            scene_title: Scene title for context
            duration: Expected scene duration
            
        Returns:
            Detailed instruction prompt for browser_subagent
        """
        instructions = f"""Execute this product demo scene: "{scene_title}"

**Recording Requirements**:
- Start recording immediately when browser opens
- Record for approximately {duration} seconds
- Save recording as WebP video format
- Capture at 1920x1080 resolution if possible

**Actions to Perform**:
"""
        
        for i, action in enumerate(actions, 1):
            instructions += f"{i}. {action}\n"
        
        instructions += f"""
**Important Guidelines**:
- Wait 2-3 seconds after each action for page/UI to respond
- If an element is not found, take a screenshot and note it
- If login fails, continue to next step (we'll use fallback)
- Complete all actions within {duration} seconds
- Return the path to the saved recording

**Completion Criteria**:
When all actions are complete OR {duration} seconds have elapsed, stop recording and return:
- Recording file path
- Success/failure status
- Any errors encountered
"""
        
        return instructions
    
    def record_scene(self, scene: SceneRecording) -> bool:
        """
        Record a single scene using browser_subagent
        
        Args:
            scene: SceneRecording object with actions
            
        Returns:
            True if recording succeeded, False otherwise
        """
        print(f"\n🎬 Scene {scene.scene_number}: {scene.title}")
        print(f"   Duration: {scene.duration_seconds}s")
        print(f"   Actions: {len(scene.browser_actions)}")
        
        if not scene.has_actions:
            print("   ⏭️  No browser actions (static/B-roll scene)")
            scene.status = "skipped"
            return True
        
        # Generate browser automation instructions
        instructions = self.convert_actions_to_instructions(
            scene.browser_actions,
            scene.title,
            scene.duration_seconds
        )
        
        # Define recording output path
        recording_name = f"scene_{scene.scene_number}_{scene.title.lower().replace(' ', '_')}"
        scene.recording_path = self.output_dir / f"{recording_name}.webp"
        
        print(f"   📹 Starting browser automation...")
        print(f"   📁 Target: {scene.recording_path.name}")
        
        # NOTE: This is where we would call browser_subagent
        # For now, we'll simulate and create a placeholder
        # TODO: Integrate browser_subagent tool in Phase 2 completion
        
        try:
            # Initialize Selenium
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            # Enable storage of video/screenshots if possible, or just screenshots for now?
            # Selenium doesn't natively record video easily without extensions. 
            # For this MVP, let's capture a sequence of screenshots or just the final state?
            # The requirement is "Record as WebP".
            # We can use a screen recorder wrapper or just capture screenshots.
            # To keep it simple and robust: Capture a high-res screenshot as the "video" frame 
            # since ffmpeg can take a single image and loop it. 
            # OR we can actually try to record using a virtual display.
            # Given constraints: Let's stick to taking a high-quality screenshot after actions.
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Use URL from config
            target_url = self.config.product.url if self.config else "https://example.com"
            print(f"   🌍 Navigating to: {target_url}")
            driver.get(target_url)
            
            # Handle Login if credentials exist and we are on a login page? 
            # Or just assume session is fresh.
            # For this MVP, we just navigate. 
            # If creds are needed, we might need a specific "Login" action in the storyline logic.
            
            time.sleep(3) # Wait for load
            
            # Let's perform the actions using Selenium
            print(f"   📹 Starting browser automation with Selenium...")
            
            # Create temp dir for frames
            temp_frames_dir = self.output_dir / "temp_frames" / f"scene_{scene.scene_number}"
            if temp_frames_dir.exists():
                shutil.rmtree(temp_frames_dir)
            temp_frames_dir.mkdir(parents=True, exist_ok=True)
            
            # Action Queue
            action_queue = list(scene.browser_actions)
            frame_count = 0
            start_time = time.time()
            max_duration = scene.duration_seconds if scene.duration_seconds > 0 else 10
            
            # Action timing control
            current_action_idx = 0
            last_action_time = start_time
            action_interval = 2.0 # Minimum seconds between actions
            
            print(f"   🎥 Starting interleaved capture/action loop...")
            
            while True:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Check exit conditions
                if not action_queue and elapsed > (max_duration if max_duration > 15 else 5): 
                    # If actions done and we recorded enough (min 5s or duration), break
                    break
                
                if elapsed > max_duration + 10: # Safety timeout
                    break
                    
                # 1. Capture Frame
                try:
                    filename = temp_frames_dir / f"frame_{frame_count:05d}.png"
                    driver.save_screenshot(str(filename))
                    frame_count += 1
                except Exception as e:
                    print(f"      Frame capture warning: {e}")
                
                # 2. Execute Next Action (if ready)
                if action_queue and (current_time - last_action_time > action_interval):
                    action = action_queue.pop(0)
                    print(f"   ▶️  Executing: {action}")
                    try:
                        self.execute_action(driver, action)
                        # Capture immediately after action
                        filename = temp_frames_dir / f"frame_{frame_count:05d}.png"
                        driver.save_screenshot(str(filename))
                        frame_count += 1
                    except Exception as e:
                         print(f"      Action failed: {e}")
                    
                    last_action_time = time.time()
                    
                # Throttle loop to ~5 FPS
                time.sleep(0.2) 
            
            print(f"   🛑 Recording finished. Frames: {frame_count}")
            
            driver.quit()
            
            # Stitch video with ffmpeg
            if frame_count > 0:
                print(f"   🎞️  Stitching {frame_count} frames to video...")
                output_video = str(scene.recording_path).replace('.webp', '.mp4')
                
                # Update scene path to mp4
                scene.recording_path = Path(output_video)
                
                try:
                    # ffmpeg -framerate 5 -i frame_%05d.png -c:v libx264 -pix_fmt yuv420p output.mp4
                    cmd = [
                        "ffmpeg",
                        "-y", # Overwrite
                        "-framerate", "5",
                        "-i", str(temp_frames_dir / "frame_%05d.png"),
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                        output_video
                    ]
                    
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"   ✅ Saved video: {scene.recording_path}")
                    
                    # Cleanup frames
                    shutil.rmtree(temp_frames_dir)
                    scene.status = "success"
                    return True
                    
                except Exception as e:
                     print(f"   ❌ FFmpeg stitching failed: {e}")
                     scene.status = "failed"
                     return False
            else:
                 print("   ⚠️  No frames captured")
                 scene.status = "failed"
                 return False
            
        except Exception as e:
            print(f"   ❌ Recording failed: {e}")
            scene.status = "failed"
            scene.error_message = str(e)
            return False

    def execute_action(self, driver: webdriver.Chrome, action: str):
        """Parse and execute a single browser action"""
        print(f"      Running: {action}")
        action = action.strip()
        
        try:
            if action.lower().startswith("wait"):
                # Parse "Wait X seconds"
                parts = action.split()
                seconds = 2
                for part in parts:
                    if part.isdigit():
                        seconds = int(part)
                        break
                time.sleep(seconds)
                
            elif action.lower().startswith("click"):
                # Parse "Click [Text]..."
                target = action[5:].strip()
                # Remove "button", "link" etc if present to just get the text/id
                # Heuristic: Try to find by text content first
                
                # Check for quotes
                if "'" in target:
                    target_text = target.split("'")[1]
                elif '"' in target:
                    target_text = target.split('"')[1]
                else:
                    target_text = target
                
                # Try XPATH for text matching
                try:
                    el = driver.find_element(By.XPATH, f"//*[contains(text(), '{target_text}')]")
                    driver.execute_script("arguments[0].scrollIntoView(true);", el)
                    time.sleep(0.5)
                    el.click()
                    return
                except:
                    pass
                    
                # Try partial match or other selectors
                try:
                    el = driver.find_element(By.PARTIAL_LINK_TEXT, target_text)
                    el.click()
                    return
                except:
                    print(f"      ⚠️ Could not click: {target_text}")
                    
            elif action.lower().startswith("type"):
                # Parse "Type 'text' in [Element]"
                # Simple extraction: find string between quotes, then finding the rest
                import re
                matches = re.findall(r"['\"](.*?)['\"]", action)
                if len(matches) >= 1:
                    text_to_type = matches[0]
                    # Target element might be the second match or implied?
                    # If len matches >= 2, second is target.
                    
                    target_el = None
                    if len(matches) >= 2:
                        target_name = matches[1]
                        # Try to find input by placeholder or label?
                        try:
                            target_el = driver.find_element(By.XPATH, f"//input[@placeholder='{target_name}']")
                        except:
                            try:
                                target_el = driver.find_element(By.XPATH, f"//input[@name='{target_name}']")
                            except:
                                pass
                    
                    if not target_el:
                         # Fallback: Find first visible input? dangerous.
                         # Try finding focused element?
                         try:
                             target_el = driver.switch_to.active_element
                         except:
                             pass
                             
                    if target_el:
                        target_el.clear()
                        target_el.send_keys(text_to_type)
                    else:
                        print(f"      ⚠️ Could not find input to type: {text_to_type}")
                        
            elif action.lower().startswith("navigate"):
                # "Navigate to [URL]"
                if "http" in action:
                    url = action.split("yyy")[-1] # simplistic
                    # Extract URL
                    import re
                    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', action)
                    if urls:
                        driver.get(urls[0])
                        
        except Exception as e:
            print(f"      ❌ Action error: {e}")
    
    def generate_manifest(self, scenes: List[SceneRecording], output_path: Path):
        """Generate JSON manifest of all recordings"""
        manifest = {
            "generated": datetime.now().isoformat(),
            "total_scenes": len(scenes),
            "recorded_scenes": sum(1 for s in scenes if s.status in ["success", "pending_integration"]),
            "scenes": []
        }
        
        for scene in scenes:
            scene_data = {
                "scene_number": scene.scene_number,
                "title": scene.title,
                "duration": scene.duration_seconds,
                "has_actions": scene.has_actions,
                "status": scene.status,
                "recording_path": str(scene.recording_path) if scene.recording_path else None,
                "error": scene.error_message
            }
            manifest["scenes"].append(scene_data)
        
        output_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print(f"\n📄 Manifest saved: {output_path}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous browser recording from storyline")
    parser.add_argument(
        "--storyline",
        default="../INPUT/configuration/Product_Specs.md",
        help="Path to Product_Specs.md (or Storyline.md)"
    )
    parser.add_argument(
        "--config",
        default="../INPUT/configuration/Product_Specs.md",
        help="Path to Product_Specs.md"
    )
    parser.add_argument(
        "--output-dir",
        default="../01_raw_recordings",
        help="Output directory for recordings"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    storyline_path = Path(__file__).parent / args.storyline
    config_path = Path(__file__).parent / args.config
    output_dir = Path(__file__).parent / args.output_dir
    
    print("="*80)
    print("🎬 AUTONOMOUS BROWSER RECORDING SYSTEM")
    print("="*80)
    print(f"Storyline: {storyline_path}")
    print(f"Output: {output_dir}")
    print()
    
    # Parse storyline
    print("📖 Parsing storyline...")
    parser = StorylineParser(storyline_path)
    scenes = parser.parse_scenes()
    print(f"✅ Found {len(scenes)} scenes")
    print()
    
    # Record each scene
    from config_loader import load_config
    config = load_config(str(config_path))
    recorder = BrowserRecorder(output_dir, config)
    
    for scene in scenes:
        recorder.record_scene(scene)
    
    # Generate manifest
    manifest_path = output_dir / "recording_manifest.json"
    recorder.generate_manifest(scenes, manifest_path)
    
    # Summary
    print()
    print("="*80)
    print("📊 RECORDING SUMMARY")
    print("="*80)
    
    successful = sum(1 for s in scenes if s.status in ["success", "pending_integration"])
    skipped = sum(1 for s in scenes if s.status == "skipped")
    failed = sum(1 for s in scenes if s.status == "failed")
    
    print(f"✅ Successful: {successful}")
    print(f"⏭️  Skipped (no actions): {skipped}")
    print(f"❌ Failed: {failed}")
    print()
    
    print("🎯 Next Steps:")
    print("   1. Review recording_manifest.json")
    print("   2. Integrate browser_subagent tool for actual recording")
    print("   3. Run voiceover generation: python3 voiceover_generator.py --storyline")
    print()


if __name__ == "__main__":
    main()
