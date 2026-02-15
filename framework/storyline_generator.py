#!/usr/bin/env python3
"""
Storyline Intelligence Engine

Autonomous product analysis and PSB (Problem-Solution-Benefit) storyline creation.

Workflow:
1. Read Product_Specs.json for brand, product URL, value props
2. Launch browser agent to explore product
3. Identify key UI elements and interaction points
4. Analyze PSB structure (Problem → Solution → Benefit)
5. Generate hook-driven opening
6. Output comprehensive Storyline.md

This is the CORE intelligence module - all downstream processes (recording, 
voiceover, captions, composition) work from the Storyline.md output.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import yaml
import re
from dataclasses import dataclass, field
from datetime import datetime

# Add parent to path for config_loader
sys.path.insert(0, str(Path(__file__).parent))
from config_loader import load_config, DemoConfig

# Gemini API
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("⚠️  Warning: google.genai not installed. Install with: pip install google-genai")
    genai = None


@dataclass
class StorylineScene:
    """Represents a single scene in the storyline"""
    scene_number: int
    title: str
    duration_seconds: int
    browser_actions: List[str] = field(default_factory=list)
    voiceover_script: str = ""
    captions: List[str] = field(default_factory=list)
    visual_notes: str = ""


@dataclass
class Storyline:
    """Complete product demo storyline"""
    product_name: str
    total_duration: int
    hook_type: str
    structure: str  # e.g., "Problem (30s) → Solution (60s) → Benefit (30s)"
    scenes: List[StorylineScene] = field(default_factory=list)


class StorylineGenerator:
    """Generates intelligent product demo storylines"""
    
    def __init__(self, config: DemoConfig):
        self.config = config
        # ProductInfo has: name, tagline, url, repository, category, problem, solution
        self.product_url = config.product.url
        self.product_name = config.product.name
        self.product_tagline = config.product.tagline
        self.product_problem = config.product.problem
        self.product_solution = config.product.solution
        self.product_category = config.product.category
        
        # Initialize Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.gemini_client = genai.Client(api_key=api_key)
    
    def analyze_product(self) -> Dict:
        """
        Analyze product to extract PSB elements
        
        Returns:
            Dict with 'problem', 'solution', 'benefit' keys
        """
        print("🔍 Analyzing product for PSB structure...")
        
        prompt = f"""Analyze this product and extract PSB (Problem-Solution-Benefit) elements:

Product: {self.product_name}
Tagline: {self.product_tagline}
URL: {self.product_url}
Category: {self.product_category}
Problem: {self.product_problem}
Solution: {self.product_solution}

Extract:
1. **Problem**: What pain point does this solve? (1-2 sentences, include shocking statistics if possible)
2. **Solution**: What is the core solution? (1-2 sentences, focus on the unique approach)
3. **Benefit**: What are the measurable outcomes? (1-2 sentences, use numbers/metrics)

Return as JSON:
{{
    "problem": "...",
    "solution": "...",
    "benefit": "...",
    "hook_suggestion": "Opening line that grabs attention (question, stat, or bold claim)"
}}
"""
        
        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json",
                )
            )
            
            import json
            psb_data = json.loads(response.text)
            print(f"✅ PSB Analysis Complete")
            print(f"   Problem: {psb_data['problem'][:80]}...")
            print(f"   Solution: {psb_data['solution'][:80]}...")
            
            return psb_data
            
        except Exception as e:
            print(f"⚠️  PSB analysis failed: {e}")
            # Fallback to basic extraction
            # Fallback PSB without specific attributes
            return {
                "problem": self.product_problem,
                "solution": self.product_solution,
                "benefit": "Save time and reduce costs significantly",
                "hook_suggestion": f"Discover how {self.product_name} transforms your workflow"
            }
    
    def explore_product_ui(self) -> Dict:
        """
        Use browser automation to explore product and identify interaction points
        
        Returns:
            Dict with UI elements and suggested interaction flow
        """
        print(f"🌐 Exploring product UI: {self.product_url}")
        
        # For now, use Gemini to suggest likely UI elements based on product type
        # TODO: Implement actual browser automation in Phase 2
        
        prompt = f"""Given this product, suggest the key UI interaction flow for a demo:

Product: {self.product_name}
URL: {self.product_url}
Category: {self.product_category}
Problem: {self.product_problem}
Solution: {self.product_solution}

Suggest a realistic user journey based on the product's specific problem/solution. Do not assume a generic SaaS "Dashboard" or "Campaign" creation flow unless the product specifically mentions it.

Define the flow for these phases:
1. Landing page (what viewer sees first about the problem/solution)
2. Access/Entry (how user starts using the product - e.g., 'Get Started', 'Login', or 'Search')
3. Core Interaction (The main "Aha!" moment where the problem is solved)
4. Result/Benefit (The final output or dashboard view)

Return as JSON with this structure:
{{
    "landing": {{
        "actions": ["Navigate to {{self.product_url}}", "Observe 'Hero Headline'"],
        "key_elements": ["Key Value Prop", "Call to Action"]
    }},
    "authentication": {{
        "actions": ["Click 'Get Started' or 'Login'", "Enter credentials if applicable"],
        "key_elements": ["Entry point"]
    }},
    "feature_demo": {{
        "actions": ["Action 1 (e.g., Search for X)", "Action 2 (e.g., Click result)", "Action 3"],
        "key_elements": ["Core feature interface"]
    }},
    "results": {{
        "actions": ["View final report/dashboard"],
        "key_elements": ["Success metrics", "Export options"]
    }}
}}
"""
        
        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4, # Lower temperature for more grounded output
                    response_mime_type="application/json",
                )
            )
            
            import json
            ui_flow = json.loads(response.text)
            print(f"✅ UI Flow Mapped")
            print(f"   Phases: {', '.join(ui_flow.keys())}")
            
            return ui_flow
            
        except Exception as e:
            print(f"⚠️  UI exploration failed: {e}")
            return {
                "landing": {
                    "actions": [f"Navigate to {self.product_url}"],
                    "key_elements": ["Hero section"]
                }
            }
    
    def generate_scene_scripts(self, psb_data: Dict, ui_flow: Dict) -> List[StorylineScene]:
        """
        Generate detailed scripts for each scene based on PSB and UI flow
        """
        print("📝 Generating scene-by-scene storyline...")
        
        # Check for recording manifest to align script with reality
        manifest_path = Path(__file__).parent.parent / "INPUT/raw_recordings/recording_manifest.json"
        recording_context = ""
        if manifest_path.exists():
             try:
                 import json
                 manifest = json.loads(manifest_path.read_text())
                 recording_context = "\n**Recording Reality (Align script with this):**\n"
                 for scene in manifest['scenes']:
                     status = scene.get('status', 'unknown')
                     recording_context += f"- Scene {scene['scene_number']}: {status.upper()}"
                     if scene.get('error'):
                         recording_context += f" (Error: {scene['error']})"
                     recording_context += "\n"
             except:
                 pass

        target_duration = self.config.demo.duration_seconds
        navigability = getattr(self.config.demo, 'navigability_status', 'full')
        
        if navigability == 'limited':
            structure_prompt = (
                "**Constraint**: The product has LIMITED public navigability (likely just a landing page).\n"
                "Create a concise **1 to 3 scene** demo.\n"
                "- Scene 1: Hook + Problem (Focus on the pain point)\n"
                "- Scene 2: Solution Value Prop (Show the landing page and explain how it solves the problem)\n"
                "- Scene 3 (Optional): Impact/CTA (Summary and call to action)\n"
                "\n"
                "**CRITICAL**: Do NOT attempt to simulate complex dashboard interactions or features that are likely behind a login. Focus on the available public content."
            )
        else:
            structure_prompt = (
                "Create 5 scenes following this timing:\n"
                "1. Hook + Problem (30s) - Grab attention, establish pain\n"
                "2. Solution Introduction (20s) - Show landing page, introduce product\n"
                "3. Feature Demo (60s) - Live product interaction showing key workflow\n"
                "4. Results Showcase (20s) - Show output/benefit\n"
                "5. Impact + CTA (20s) - Metrics and call-to-action"
            )

        # Construct prompt safely to avoid syntax errors with triple quotes
        prompt_parts = [
            f"Create a {target_duration}-second product demo script with this structure:",
            "",
            "**Context**:",
            recording_context,
            "",
            "**PSB Analysis**:",
            f"- Problem: {psb_data['problem']}",
            f"- Solution: {psb_data['solution']}",
            f"- Benefit: {psb_data['benefit']}",
            f"- Hook: {psb_data['hook_suggestion']}",
            "",
            f"**Product**: {self.product_name}",
            f"**Target Duration**: {target_duration}s",
            f"**Tone**: {self.config.voiceover.tone}",
            f"**Navigability**: {navigability}",
            "",
            "**UI Flow Available**:",
            yaml.dump(ui_flow, default_flow_style=False),
            "",
            structure_prompt,
            "",
            "For EACH scene, provide:",
            "- Scene title",
            "- Duration in seconds",
            "- **Voiceover script**: ",
            f"    - MUST be natural and conversational ({self.config.voiceover.pacing_wpm} WPM).",
            "    - **CRITICAL**: Use emotion tags at the start of sentences, e.g., `[excited]`, `[concerned]`, `[proud]`, `[happy]`, `[calm]`.",
            "    - Narrate what is happening on screen (Video).",
            "- 3-5 caption keywords (short phrases for on-screen text)",
            "- Visual description (what's shown on screen)",
            "",
            "Return as JSON array:",
            "[",
            "    {",
            '        "scene_number": 1,',
            '        "title": "Hook + Problem",',
            '        "duration_seconds": 30,',
            '        "voiceover_script": "[concerned] Are you tired of... [excited] We have a solution!",',
            '        "captions": ["keyword1", "keyword2"],',
            '        "visual_notes": "What viewer sees on screen"',
            "    },",
            "    ...",
            "]"
        ]
        
        prompt = "\n".join(prompt_parts)
        
        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    response_mime_type="application/json",
                )
            )
            
            import json
            scenes_data = json.loads(response.text)
            
            scenes = []
            for scene_data in scenes_data:
                # Map UI actions to scene
                browser_actions = []
                if scene_data['scene_number'] == 2:  # Landing
                    browser_actions = ui_flow.get('landing', {}).get('actions', [])
                elif scene_data['scene_number'] == 3:  # Feature demo
                    auth_actions = ui_flow.get('authentication', {}).get('actions', [])
                    demo_actions = ui_flow.get('feature_demo', {}).get('actions', [])
                    browser_actions = auth_actions + demo_actions
                elif scene_data['scene_number'] == 4:  # Results
                    browser_actions = ui_flow.get('results', {}).get('actions', [])
                
                scene = StorylineScene(
                    scene_number=scene_data['scene_number'],
                    title=scene_data['title'],
                    duration_seconds=scene_data['duration_seconds'],
                    voiceover_script=scene_data['voiceover_script'],
                    captions=scene_data.get('captions', []),
                    visual_notes=scene_data.get('visual_notes', ''),
                    browser_actions=browser_actions
                )
                scenes.append(scene)
            
            print(f"✅ Generated {len(scenes)} scenes")
            return scenes
            
        except Exception as e:
            print(f"❌ Scene generation failed: {e}")
            raise
    
    def export_storyline_md(self, storyline: Storyline, output_path: Path):
        """Export storyline to Markdown format"""
        
        content = f"""# Product Demo Storyline: {storyline.product_name}

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Meta
- **Total Duration**: {storyline.total_duration}s
- **Hook Type**: {storyline.hook_type}
- **Structure**: {storyline.structure}
- **Tone**: {self.config.voiceover.tone}

---

"""
        
        for scene in storyline.scenes:
            content += f"""## Scene {scene.scene_number}: {scene.title}
**Duration**: {scene.duration_seconds}s

### Browser Actions
"""
            if scene.browser_actions:
                for action in scene.browser_actions:
                    content += f"- {action}\n"
            else:
                content += "- N/A (B-roll or static content)\n"
            
            content += f"""
### Voiceover Script
{scene.voiceover_script}

### Captions
{', '.join([f'"{cap}"' for cap in scene.captions])}

### Visual Notes
{scene.visual_notes}

---

"""
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')
        print(f"✅ Storyline exported to: {output_path}")
    
    def generate(self, output_path: Optional[Path] = None) -> Storyline:
        """
        Main generation workflow
        
        Returns:
            Storyline object
        """
        print("="*80)
        print("🎬 STORYLINE INTELLIGENCE ENGINE")
        print("="*80)
        print(f"Product: {self.product_name}")
        print(f"URL: {self.product_url}")
        print(f"Target Duration: {self.config.demo.duration_seconds}s")
        print()
        
        # Step 1: PSB Analysis
        psb_data = self.analyze_product()
        print()
        
        # Step 2: UI Exploration
        ui_flow = self.explore_product_ui()
        print()
        
        # Step 3: Scene Generation
        scenes = self.generate_scene_scripts(psb_data, ui_flow)
        print()
        
        # Step 4: Create Storyline object
        storyline = Storyline(
            product_name=self.product_name,
            total_duration=self.config.demo.duration_seconds,
            hook_type=psb_data.get('hook_suggestion', 'Problem-focused'),

            structure=f"Problem ({scenes[0].duration_seconds}s) → Solution ({scenes[1].duration_seconds}s) ..." if len(scenes) > 1 else "Single Scene",
            scenes=scenes
        )
        
        # Step 5: Export to Markdown
        if output_path is None:
            output_path = Path(__file__).parent.parent / "OUTPUT" / "scripts" / "Storyline.md"
        
        self.export_storyline_md(storyline, output_path)
        
        print()
        print("="*80)
        print("✅ STORYLINE GENERATION COMPLETE")
        print("="*80)
        print(f"📁 Output: {output_path}")
        print(f"📊 Scenes: {len(storyline.scenes)}")
        print(f"⏱️  Total Duration: {storyline.total_duration}s")
        print()
        
        return storyline


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate product demo storyline")
    parser.add_argument(
        "--config",
        default="../INPUT/configuration/Product_Specs.json",
        help="Path to Product_Specs.json"
    )
    parser.add_argument(
        "--output",
        default="../OUTPUT/scripts/Storyline.md",
        help="Output path for Storyline.md"
    )
    
    args = parser.parse_args()
    
    # Strip quotes and whitespace if present
    config_arg = args.config.strip('"').strip("'").strip()
    
    # Load config
    # Fix: Correctly handle absolute paths and CWD-relative paths
    if Path(config_arg).is_absolute():
        config_path = Path(config_arg)
    elif (Path.cwd() / config_arg).exists():
        config_path = Path.cwd() / config_arg
    else:
        config_path = Path(__file__).parent / config_arg
        
    if not config_path.exists():
        # Last ditch effort: Try relative to project root (assuming framework/..)
        potential_path = Path(__file__).parent.parent / args.config
        if potential_path.exists():
            config_path = potential_path
            
    if not config_path.exists():
        print(f"❌ Config file not found: {args.config}")
        print(f"   Checked absolute, CWD ({Path.cwd()}), and relative to script ({Path(__file__).parent})")
        sys.exit(1)
    
    print(f"📄 Loading config from: {config_path}")
    config = load_config(str(config_path))
    
    # Generate storyline
    generator = StorylineGenerator(config)
    output_path = Path(__file__).parent / args.output
    storyline = generator.generate(output_path)
    
    print("🎯 Next steps:")
    print("   1. Review Storyline.md")
    print("   2. Run browser recording: python3 browser_recorder.py")
    print("   3. Generate voiceover: python3 skills/voiceover_generator/agent.py --storyline")
    print()


if __name__ == "__main__":
    main()
