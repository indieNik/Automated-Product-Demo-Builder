#!/usr/bin/env python3
"""
Technology Stack Scanner

Deep scans the project to identify all technologies used, especially Gemini models.
Used to generate technical callout scene in demo video.
"""

import re
from pathlib import Path
from typing import Dict, List
import json


class TechnologyScanner:
    """Scans project for technology usage"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.technologies = {}
    
    def scan_gemini_models(self) -> Dict[str, str]:
        """Scan all Python files for Gemini model references"""
        gemini_models = {}
        
        # Pattern to find Gemini model strings
        model_pattern = r'["\']?(gemini-(?:exp-)?[\d\.]+-(?:flash|pro|thinking)(?:-preview)?(?:-\d+)?)["\']?'
        
        for py_file in self.project_root.rglob("*.py"):
            if ".venv" in str(py_file) or "node_modules" in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Find all Gemini model references
                matches = re.findall(model_pattern, content, re.IGNORECASE)
                
                for model in matches:
                    # Parse model name for display
                    if "flash" in model.lower():
                        display_name = f"Gemini {model.split('-')[1]} Flash"
                        purpose = self._infer_purpose(py_file, content, model)
                    elif "pro" in model.lower():
                        display_name = f"Gemini {model.split('-')[1]} Pro"
                        purpose = self._infer_purpose(py_file, content, model)
                    elif "thinking" in model.lower():
                        display_name = f"Gemini {model.split('-')[1]} Thinking"
                        purpose = self._infer_purpose(py_file, content, model)
                    else:
                        display_name = f"Gemini {model}"
                        purpose = "AI Processing"
                    
                    gemini_models[display_name] = purpose
            
            except Exception as e:
                continue
        
        return gemini_models
    
    def _infer_purpose(self, file_path: Path, content: str, model: str) -> str:
        """Infer what the model is used for based on context"""
        file_name = file_path.stem.lower()
        
        # Check filename
        if "storyline" in file_name or "generator" in file_name:
            return "Storyline Intelligence"
        elif "scene" in file_name:
            return "Scene Generation"
        elif "image" in file_name or "vision" in file_name:
            return "Image Generation"
        elif "video" in file_name:
            return "Video Generation"
        elif "caption" in file_name or "stt" in file_name:
            return "Speech-to-Text"
        
        # Check file content for clues
        if "image" in content and "generate" in content:
            return "Image Generation"
        elif "text" in content and "generate" in content:
            return "Content Generation"
        elif "analyze" in content or "analysis" in content:
            return "Analysis & Intelligence"
        
        return "AI Processing"
    
    def scan_elevenlabs_usage(self) -> Dict[str, str]:
        """Detect ElevenLabs usage"""
        elevenlabs_tech = {}
        
        for py_file in self.project_root.rglob("*.py"):
            if ".venv" in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                
                if "elevenlabs" in content.lower():
                    # Find model/version
                    if "eleven_turbo_v2" in content or "v2.5" in content:
                        elevenlabs_tech["ElevenLabs Turbo v2.5"] = "Voice Synthesis (Monika)"
                    elif "eleven_v3" in content:
                        elevenlabs_tech["ElevenLabs v3"] = "Emotional Voice Synthesis"
                    else:
                        elevenlabs_tech["ElevenLabs"] = "Text-to-Speech"
                    
                    break
            except:
                continue
        
        return elevenlabs_tech
    
    def scan_google_cloud_services(self) -> Dict[str, str]:
        """Detect Google Cloud services"""
        services = {}
        
        # Check for Firebase
        firebase_json = self.project_root / "firebase.json"
        if firebase_json.exists():
            services["Firebase Hosting"] = "Frontend CDN"
            services["Firebase Auth"] = "User Authentication"
            services["Firebase Firestore"] = "Database"
            services["Firebase Storage"] = "File Storage"
        
        # Check for Cloud Run
        for file in self.project_root.rglob("*deploy*.sh"):
            content = file.read_text()
            if "cloud run" in content.lower() or "gcloud run" in content:
                services["Google Cloud Run"] = "Backend Hosting"
                break
        
        # Check for Vertex AI
        for py_file in self.project_root.rglob("*.py"):
            if ".venv" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                if "vertex" in content.lower() or "aiplatform" in content:
                    services["Vertex AI"] = "AI Platform"
                    break
            except:
                continue
        
        return services
    
    def scan_frontend_tech(self) -> Dict[str, str]:
        """Detect frontend technologies"""
        tech = {}
        
        # Check package.json
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                if "@angular/core" in deps:
                    version = deps["@angular/core"].replace("^", "").replace("~", "")
                    tech[f"Angular {version.split('.')[0]}"] = "Frontend Framework"
                
                if "next" in deps:
                    tech["Next.js"] = "Landing Page Framework"
                
                if "typescript" in deps:
                    tech["TypeScript"] = "Type Safety"
            except:
                pass
        
        return tech
    
    def scan_video_processing(self) -> Dict[str, str]:
        """Detect video processing tools"""
        tech = {}
        
        # Check for FFmpeg usage
        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "ffmpeg" in content.lower():
                    tech["FFmpeg"] = "Video Processing"
                    break
            except:
                continue
        
        return tech
    
    def scan_all(self) -> Dict[str, str]:
        """Perform complete technology scan"""
        print("🔍 Scanning project for technologies...")
        
        all_tech = {}
        
        # Scan each category
        gemini = self.scan_gemini_models()
        elevenlabs = self.scan_elevenlabs_usage()
        gcp = self.scan_google_cloud_services()
        frontend = self.scan_frontend_tech()
        video = self.scan_video_processing()
        
        # Merge all
        all_tech.update(gemini)
        all_tech.update(elevenlabs)
        all_tech.update(gcp)
        all_tech.update(frontend)
        all_tech.update(video)
        
        # Add Python
        all_tech["Python 3.13"] = "Core Framework"
        
        print(f"✅ Found {len(all_tech)} technologies")
        
        return all_tech
    
    def generate_tech_callout_script(self, technologies: Dict[str, str]) -> str:
        """Generate voiceover script for tech stack scene"""
        
        # Group by category
        gemini_tech = {k: v for k, v in technologies.items() if "Gemini" in k}
        google_tech = {k: v for k, v in technologies.items() if "Google" in k or "Firebase" in k or "Vertex" in k}
        other_tech = {k: v for k, v in technologies.items() if k not in gemini_tech and k not in google_tech}
        
        script = "[excited] This demo was powered entirely by Google's AI ecosystem!\n\n"
        
        # Gemini models
        if gemini_tech:
            script += "We use "
            gemini_list = [f"{name} for {purpose}" for name, purpose in gemini_tech.items()]
            if len(gemini_list) == 1:
                script += gemini_list[0]
            elif len(gemini_list) == 2:
                script += f"{gemini_list[0]} and {gemini_list[1]}"
            else:
                script += ", ".join(gemini_list[:-1]) + f", and {gemini_list[-1]}"
            script += ".\n\n"
        
        # Voice synthesis
        if "ElevenLabs" in str(other_tech):
            script += "[happy] The natural voice you're hearing? Powered by ElevenLabs v3 with emotional expression capabilities.\n\n"
        
        # Google Cloud
        if google_tech:
            script += "[enthusiastic] All running seamlessly on "
            gcp_list = list(google_tech.keys())
            if len(gcp_list) == 1:
                script += gcp_list[0]
            elif len(gcp_list) == 2:
                script += f"{gcp_list[0]} and {gcp_list[1]}"
            else:
                script += ", ".join(gcp_list[:-1]) + f", and {gcp_list[-1]}"
            script += "!\n\n"
        
        script += "[proud] A complete AI-powered stack for autonomous content creation!"
        
        return script


def main():
    """Test scanner"""
    import sys
    
    # Get project root
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        # Assume we're in PRODUCT_DEMO/framework
        project_root = Path(__file__).parent.parent.parent
    
    print(f"Scanning: {project_root}")
    print()
    
    scanner = TechnologyScanner(project_root)
    technologies = scanner.scan_all()
    
    print("\n" + "="*80)
    print("🎯 DETECTED TECHNOLOGIES")
    print("="*80)
    
    for tech, purpose in sorted(technologies.items()):
        print(f"  • {tech:<30} → {purpose}")
    
    print("\n" + "="*80)
    print("🎙️  TECH CALLOUT SCRIPT")
    print("="*80)
    print()
    print(scanner.generate_tech_callout_script(technologies))
    print()


if __name__ == "__main__":
    main()
