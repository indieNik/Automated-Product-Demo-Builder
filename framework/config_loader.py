"""
Configuration Loader

Parses Product_Specs.md into structured Python objects for framework consumption.
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ProductInfo(BaseModel):
    """Product basic information"""
    name: str
    tagline: str
    url: str
    repository: Optional[str] = None
    category: str
    problem: str
    solution: str


class DemoScene(BaseModel):
    """Individual scene configuration"""
    name: str
    duration: str  # Format: "0:00-0:30"
    objective: str
    visuals: str
    key_points: List[str]
    actions: List[str] = Field(default_factory=list)
    narration: Optional[str] = None
    
    @property
    def start_seconds(self) -> int:
        """Convert start time to seconds"""
        start = self.duration.split('-')[0]
        parts = start.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    
    @property
    def end_seconds(self) -> int:
        """Convert end time to seconds"""
        end = self.duration.split('-')[1]
        parts = end.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    
    @property
    def duration_seconds(self) -> int:
        """Scene duration in seconds"""
        return self.end_seconds - self.start_seconds


class DemoStructure(BaseModel):
    """Demo configuration"""
    duration_seconds: int
    scenes: List[DemoScene]


class JudgingCriterion(BaseModel):
    """Judging criterion with weight and strategies"""
    weight: float
    strategies: List[str]


class JudgingCriteria(BaseModel):
    """All judging criteria"""
    technical_execution: JudgingCriterion
    potential_impact: JudgingCriterion
    innovation: JudgingCriterion
    presentation: JudgingCriterion


class VoiceoverSettings(BaseModel):
    """ElevenLabs voiceover configuration"""
    voice_id: str = "EaBs7G1VibMrNAuz2Na7"  # Monika - professional female narrator
    tone: str = "Confident, professional, and enthusiastic"
    pacing_wpm: int = 145
    stability: float = 0.5  # V3 requires: 0.0 (Creative), 0.5 (Natural), 1.0 (Robust)
    clarity: float = 0.7580
    style: float = 0.25


class AssetRequirements(BaseModel):
    """Required assets for video production"""
    bgm_track: Optional[str] = None
    architecture_diagram: Optional[str] = None
    test_credentials: Dict[str, str] = Field(default_factory=dict)


class DemoConfig(BaseModel):
    """Complete demo configuration"""
    product: ProductInfo
    demo: DemoStructure
    judging_criteria: JudgingCriteria
    voiceover: VoiceoverSettings
    assets: AssetRequirements


def extract_yaml_blocks(content: str) -> Dict[str, any]:
    """Extract YAML code blocks from markdown"""
    yaml_pattern = r'```yaml\n(.*?)\n```'
    matches = re.findall(yaml_pattern, content, re.DOTALL)
    
    result = {}
    for match in matches:
        try:
            data = yaml.safe_load(match)
            result.update(data)
        except yaml.YAMLError:
            continue
    
    return result


def parse_markdown_section(content: str, heading: str) -> str:
    """Extract content under a specific markdown heading"""
    pattern = rf'#{1,6}\s+{re.escape(heading)}.*?\n(.*?)(?=\n#{1,6}\s+|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def parse_scenes_from_markdown(content: str) -> List[DemoScene]:
    """Parse scene breakdown from markdown"""
    scenes = []
    
    # Find all scene sections (#### Scene N: ...)
    scene_pattern = r'####\s+Scene\s+\d+:\s+(.*?)\s+\(([\d:]+)-([\d:]+)\)(.*?)(?=####\s+Scene\s+\d+:|###\s+|##\s+|\Z)'
    matches = re.finditer(scene_pattern, content, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        name = match.group(1).strip()
        start_time = match.group(2)
        end_time = match.group(3)
        scene_content = match.group(4).strip()
        
        # Extract objective
        objective_match = re.search(r'\*\*Objective:\*\*\s+(.*?)(?=\n\*\*|\n---|\Z)', scene_content, re.DOTALL)
        objective = objective_match.group(1).strip() if objective_match else ""
        
        # Extract visuals
        visuals_match = re.search(r'\*\*Visuals:\*\*\s+(.*?)(?=\n\*\*|\n---|\Z)', scene_content, re.DOTALL)
        visuals = visuals_match.group(1).strip() if visuals_match else ""
        
        # Extract key points (bulleted list)
        key_points = []
        key_points_match = re.search(r'\*\*Key Points:\*\*\s*\n(.*?)(?=\n\*\*|\n---|\Z)', scene_content, re.DOTALL)
        if key_points_match:
            points_text = key_points_match.group(1)
            key_points = [p.strip('- ').strip() for p in points_text.split('\n') if p.strip().startswith('-')]
        
        # Extract actions (if present)
        actions = []
        actions_match = re.search(r'\*\*Actions?:\*\*\s*\n(.*?)(?=\n\*\*|\n---|\Z)', scene_content, re.DOTALL)
        if actions_match:
            actions_text = actions_match.group(1)
            actions = [a.strip('- ').strip() for a in actions_text.split('\n') if a.strip().startswith('-')]
        
        scenes.append(DemoScene(
            name=name,
            duration=f"{start_time}-{end_time}",
            objective=objective,
            visuals=visuals,
            key_points=key_points,
            actions=actions
        ))
    
    return scenes


def load_config(specs_path: str = "../INPUT/configuration/Product_Specs.md") -> DemoConfig:
    """
    Parse Product_Specs.md into structured configuration
    
    Args:
        specs_path: Path to Product_Specs.md file
        
    Returns:
        DemoConfig object with all configuration data
    """
    path = Path(specs_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Product specs not found: {specs_path}")
    
    content = path.read_text(encoding='utf-8')
    
    # Extract YAML blocks for structured data
    yaml_data = extract_yaml_blocks(content)
    
    # Parse product information
    product_section = parse_markdown_section(content, "Product Information")
    problem_section = parse_markdown_section(content, "Problem Statement")
    solution_section = parse_markdown_section(content, "Solution Overview")
    
    # Extract product URL
    # Handle [url] or plain url
    url_match = re.search(r'\*\*URL:\*\*\s+(?:\[)?(https?://[^\]\s]+)(?:\])?', content)
    product_url = url_match.group(1) if url_match else ""
    
    # Extract product name and tagline
    name_match = re.search(r'\*\*Product Name:\*\*\s+(.*)', content)
    tagline_match = re.search(r'\*\*Tagline:\*\*\s+"([^"]+)"', content)
    category_match = re.search(r'\*\*Category:\*\*\s+(.*)', content)
    
    product_info = ProductInfo(
        name=name_match.group(1).strip() if name_match else "",
        tagline=tagline_match.group(1).strip() if tagline_match else "",
        url=product_url,
        category=category_match.group(1).strip() if category_match else "",
        problem=problem_section[:500] if problem_section else "",  # First 500 chars
        solution=solution_section[:500] if solution_section else ""
    )
    
    # Parse scenes
    scenes = parse_scenes_from_markdown(content)
    
    demo_structure = DemoStructure(
        duration_seconds=180,  # 3 minutes default
        scenes=scenes
    )
    
    # Parse judging criteria
    tech_section = parse_markdown_section(content, "Technical Execution")
    impact_section = parse_markdown_section(content, "Potential Impact")
    innovation_section = parse_markdown_section(content, "Innovation / Wow Factor")
    presentation_section = parse_markdown_section(content, "Presentation / Demo")
    
    def extract_strategies(section: str) -> List[str]:
        """Extract strategy bullet points from section"""
        strategies = []
        demo_strategy = re.search(r'\*\*Demo Strategy:\*\*\s*\n(.*?)(?=\n#{1,6}\s+|\n---|\Z)', section, re.DOTALL)
        if demo_strategy:
            text = demo_strategy.group(1)
            strategies = [s.strip('- ').strip() for s in text.split('\n') if s.strip().startswith('-')]
        return strategies
    
    judging_criteria = JudgingCriteria(
        technical_execution=JudgingCriterion(
            weight=0.40,
            strategies=extract_strategies(tech_section)
        ),
        potential_impact=JudgingCriterion(
            weight=0.20,
            strategies=extract_strategies(impact_section)
        ),
        innovation=JudgingCriterion(
            weight=0.30,
            strategies=extract_strategies(innovation_section)
        ),
        presentation=JudgingCriterion(
            weight=0.10,
            strategies=extract_strategies(presentation_section)
        )
    )
    
    # Parse voiceover settings
    voiceover_section = parse_markdown_section(content, "Voiceover Specifications")
    voice_id_match = re.search(r'\*\*ElevenLabs Voice ID:\*\*\s+`([^`]+)`', voiceover_section)
    pacing_match = re.search(r'\*\*Pacing:\*\*\s+(\d+)-(\d+)\s+words', voiceover_section)
    
    voiceover_settings = VoiceoverSettings(
        voice_id=voice_id_match.group(1) if voice_id_match else "EaBs7G1VibMrNAuz2Na7",  # Monika
        pacing_wpm=int(pacing_match.group(1)) if pacing_match else 145
    )
    
    # Parse assets requirements
    # Don't use demo product YAML as test credentials - look for explicit test_credentials section
    test_creds_match = re.search(r'\*\*Login Credentials:\*\*\s+(.*?)(?:\n\n|\Z)', content, re.DOTALL)
    test_creds = {}
    if test_creds_match:
        creds_text = test_creds_match.group(1)
        email_match = re.search(r'(\S+@\S+)', creds_text)
        if email_match:
            parts = email_match.group(1).split('/')
            if len(parts) == 2:
                test_creds = {"email": parts[0], "password": parts[1]}
    
    assets = AssetRequirements(
        test_credentials=test_creds
    )
    
    return DemoConfig(
        product=product_info,
        demo=demo_structure,
        judging_criteria=judging_criteria,
        voiceover=voiceover_settings,
        assets=assets
    )


def print_config_summary(config: DemoConfig):
    """Print configuration summary for debugging"""
    print(f"=== Demo Configuration Summary ===")
    print(f"Product: {config.product.name}")
    print(f"URL: {config.product.url}")
    print(f"Tagline: {config.product.tagline}")
    print(f"\nDemo Duration: {config.demo.duration_seconds}s")
    print(f"Total Scenes: {len(config.demo.scenes)}")
    
    for i, scene in enumerate(config.demo.scenes, 1):
        print(f"\n  Scene {i}: {scene.name}")
        print(f"    Duration: {scene.duration} ({scene.duration_seconds}s)")
        print(f"    Objective: {scene.objective[:80]}...")
        print(f"    Key Points: {len(scene.key_points)}")
        print(f"    Actions: {len(scene.actions)}")
    
    print(f"\nVoiceover: {config.voiceover.voice_id} @ {config.voiceover.pacing_wpm} WPM")
    print(f"\nJudging Criteria:")
    print(f"  Technical: {config.judging_criteria.technical_execution.weight*100}%")
    print(f"  Impact: {config.judging_criteria.potential_impact.weight*100}%")
    print(f"  Innovation: {config.judging_criteria.innovation.weight*100}%")
    print(f"  Presentation: {config.judging_criteria.presentation.weight*100}%")


if __name__ == "__main__":
    # Test the config loader
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else "../INPUT/configuration/Product_Specs.md"
    
    try:
        config = load_config(config_path)
        print_config_summary(config)
    except Exception as e:
        print(f"Error loading config: {e}")
        import traceback
        traceback.print_exc()
