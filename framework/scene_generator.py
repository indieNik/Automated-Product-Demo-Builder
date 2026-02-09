#!/usr/bin/env python3
"""
Gemini Scene Generator

Generates professional AI-powered scenes for demo video:
- Hook scene: Problem visualization with attention-grabbing imagery
- Wrap-up scene: Technology stack showcase

Uses Gemini 2.5 Flash for image generation.
"""

import os
import sys
from pathlib import Path
from typing import Tuple
import base64

# Gemini SDK
try:
    import google.genai as genai
except ImportError:
    print("⚠️  Google GenAI SDK not installed. Install with: pip install google-genai")
    sys.exit(1)

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config_loader import load_config
from tech_scanner import TechnologyScanner


class GeminiSceneGenerator:
    """Generates AI-powered visual scenes for demo video"""
    
    def __init__(self, gemini_api_key: str):
        """Initialize Gemini client"""
        self.client = genai.Client(api_key=gemini_api_key)
        self.image_model = "gemini-2.5-flash-image"
    
    def generate_hook_scene(
        self,
        problem: str,
        hook_text: str,
        output_path: Path
    ) -> Tuple[Path, str]:
        """
        Generate attention-grabbing hook scene
        
        Args:
            problem: Product problem statement
            hook_text: Hook question/statement
            output_path: Where to save PNG
            
        Returns:
            (image_path, voiceover_script)
        """
        print("🎨 Generating Hook Scene...")
        print(f"   Problem: {problem[:80]}...")
        print(f"   Hook: {hook_text[:80]}...")
        
        # Create compelling image prompt
        image_prompt = f"""
        Create a striking, professional hook scene image for a technical product demo:
        
        Context:
        - Problem: {problem}
        - Hook: {hook_text}
        
        Visual Style:
        - Modern tech presentation aesthetic
        - Clean, minimalist design
        - Professional color palette (blues, purples, tech gradients)
        - High contrast for readability
        - No text overlays (voice will provide narration)
        
        Content:
        - Visual metaphor for the problem/pain point
        - Convey frustration or challenge
        - Relatable business/technical scenario
        - Professional photography or illustration style
        
        Examples of good approaches:
        - Overwhelmed person at computer with cluttered screen
        - Clock/calendar showing time pressure
        - Rising cost graphs
        - Scattered inefficient workflow
        
        Output: Single powerful image, 1920x1080, professional presentation quality
        """
        
        try:
            # Generate image
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=image_prompt
            )
            # response = self.client.models.generate_images(
            #     model=self.image_model,
            #     image_path=pscene
            #     prompt=image_prompt
            # )
            
            # Save image
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        # Decode and save
                        try:
                            if hasattr(part, 'as_image'):
                                img_out = part.as_image()
                            else:
                                import io
                                from PIL import Image as PILImage
                                img_out = PILImage.open(io.BytesIO(part.inline_data.data))
                                
                            img_out.save(output_path)
                            print(f"   ✅ Hook scene saved: {output_path}")
                            return output_path, f"[concerned] {hook_text}"
                        except Exception as e:
                            print(f"Failed to save image part: {e}")
                            raise e
            else:
                print("   ❌ No image generated")
                return None, hook_text
            
        except Exception as e:
            print(f"   ❌ Image generation failed: {e}")
            print(f"   Using fallback approach...")
            return None, hook_text
        
        # Create voiceover script with emotional expressions
        voiceover_script = f"[concerned] {hook_text}"
        
        return output_path, voiceover_script
    
    def generate_tech_wrapup_scene(
        self,
        technologies: dict,
        output_path: Path
    ) -> Tuple[Path, str]:
        """
        Generate technology stack showcase scene
        
        Args:
            technologies: Dict of {tech_name: purpose}
            output_path: Where to save PNG
            
        Returns:
            (image_path, voiceover_script)
        """
        print("🎨 Generating Tech Wrap-up Scene...")
        print(f"   Technologies: {len(technologies)}")
        
        # Create tech list for display
        tech_list = "\n".join([f"• {name}: {purpose}" 
                               for name, purpose in sorted(technologies.items())])
        
        # Group technologies
        gemini_tech = [k for k in technologies.keys() if "Gemini" in k]
        google_cloud = [k for k in technologies.keys() if "Google" in k or "Firebase" in k or "Vertex" in k]
        
        image_prompt = f"""
        Create a professional technology stack visualization for a technical demo wrap-up:
        
        Technologies to feature:
        {tech_list}
        
        Visual Style:
        - Modern tech presentation aesthetic
        - Clean, organized layout
        - Professional color scheme (Google AI colors: blue, green, yellow, red accents)
        - High-tech, cutting-edge feel
        - 1920x1080 presentation format
        
        Layout Requirements:
        - Prominently feature Gemini models: {', '.join(gemini_tech)}
        - Show Google Cloud ecosystem: {', '.join(google_cloud)}
        - Modern tech stack diagram or organized grid
        - Clear, scannable hierarchy
        - Professional presentation quality
        
        Content:
        - Technology logos or icons (if appropriate)
        - Clean typography
        - Grouped by category (AI, Cloud, Frontend, etc.)
        - Convey "cutting-edge AI stack"
        - No cluttered detail - focus on key tech
        
        Mood: Innovative, professional, enterprise-grade technology
        """
        
        try:
            # Generate image
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=image_prompt
            )

            # Save image
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        # Decode and save
                        try:
                            if hasattr(part, 'as_image'):
                                img_out = part.as_image()
                            else:
                                import io
                                from PIL import Image as PILImage
                                img_out = PILImage.open(io.BytesIO(part.inline_data.data))
                                
                            img_out.save(output_path)
                            print(f"   ✅ Tech wrap-up scene saved: {output_path}")
                        except Exception as e:
                            print(f"Failed to save image part: {e}")
                            raise e
            
            else:
                print("   ❌ No image generated")
                return None, ""
            
        except Exception as e:
            print(f"   ❌ Image generation failed: {e}")
            return None, ""
        
        # Generate voiceover script using scanner
        scanner = TechnologyScanner(Path.cwd())
        voiceover_script = scanner.generate_tech_callout_script(technologies)
        
        return output_path, voiceover_script


def main():
    """Test scene generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate AI scenes for demo")
    parser.add_argument(
        "--type",
        choices=["hook", "tech"],
        required=True,
        help="Scene type to generate"
    )
    parser.add_argument(
        "--output-dir",
        default="../OUTPUT/scenes",
        help="Output directory for scenes"
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        sys.exit(1)
    
    generator = GeminiSceneGenerator(api_key)
    output_dir = Path(__file__).parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.type == "hook":
        # Test hook scene
        problem = "Creating high-performing User-Generated Content (UGC) ads is incredibly expensive and time-consuming"
        hook = "Are you spending thousands and weeks on UGC ads that barely move the needle?"
        
        image_path, script = generator.generate_hook_scene(
            problem,
            hook,
            output_dir / "hook_scene.png"
        )
        
        if image_path:
            print(f"\n✅ Hook Scene Generated!")
            print(f"   Image: {image_path}")
            print(f"   Script: {script}")
    
    elif args.type == "tech":
        # Scan technologies
        project_root = Path(__file__).parent.parent.parent
        scanner = TechnologyScanner(project_root)
        technologies = scanner.scan_all()
        
        image_path, script = generator.generate_tech_wrapup_scene(
            technologies,
            output_dir / "tech_wrapup_scene.png"
        )
        
        if image_path:
            print(f"\n✅ Tech Wrap-up Scene Generated!")
            print(f"   Image: {image_path}")
            print(f"\n📝 Voiceover Script:")
            print(script)


if __name__ == "__main__":
    main()
