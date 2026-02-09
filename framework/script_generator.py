"""
Script Generator

Generates voiceover narration script from Product_Specs.md using Gemini API.
Optimized for hackathon judging criteria.
"""

import os
from google import genai
from google.genai import types
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

from config_loader import load_config, DemoConfig, DemoScene

# Load environment variables
load_dotenv()


def build_prompt_for_script_generation(config: DemoConfig) -> str:
    """
    Build Gemini prompt from configuration
    
    Structures the prompt to optimize for judging criteria:
    - Technical Execution (40%)
    - Potential Impact (20%)
    - Innovation / Wow Factor (30%)
    - Presentation / Demo (10%)
    """
    
    # Extract judging criteria strategies
    tech_strategies = "\n  - ".join(config.judging_criteria.technical_execution.strategies)
    impact_strategies = "\n  - ".join(config.judging_criteria.potential_impact.strategies)
    innovation_strategies = "\n  - ".join(config.judging_criteria.innovation.strategies)
    presentation_strategies = "\n  - ".join(config.judging_criteria.presentation.strategies)
    
    # Build scene breakdown
    scene_breakdown = []
    for i, scene in enumerate(config.demo.scenes, 1):
        scene_text = f"""
**Scene {i}: {scene.name}**
- Duration: {scene.duration} ({scene.duration_seconds} seconds)
- Objective: {scene.objective}
- Visuals: {scene.visuals}
- Key Points to Cover:
  {chr(10).join([f'  • {point}' for point in scene.key_points])}
"""
        scene_breakdown.append(scene_text.strip())
    
    scenes_text = "\n\n".join(scene_breakdown)
    
    prompt = f"""You are a technical demo scriptwriter for a hackathon submission. Your goal is to create a compelling voiceover script that maximizes the judging score.

# Product Information
**Name:** {config.product.name}
**Tagline:** {config.product.tagline}
**Category:** {config.product.category}

**Problem Being Solved:**
{config.product.problem}

**Solution:**
{config.product.solution}

---

# Judging Criteria (CRITICAL - Script Must Address All)

## Technical Execution (40% weight - HIGHEST PRIORITY)
Demonstrate quality application development, deep Gemini 3 integration, code quality, and functionality.

**Strategies to incorporate:**
  - {tech_strategies}

## Potential Impact (20% weight)
Show real-world problem scope, market applicability, and solution efficiency.

**Strategies to incorporate:**
  - {impact_strategies}

## Innovation / Wow Factor (30% weight)
Highlight novel approach, unique solution, and competitive differentiation.

**Strategies to incorporate:**
  - {innovation_strategies}

## Presentation / Demo (10% weight)
Clear problem definition, effective solution presentation, Gemini 3 usage explanation.

**Strategies to incorporate:**
  - {presentation_strategies}

---

# Scene Breakdown (Total: {config.demo.duration_seconds} seconds)

{scenes_text}

---

# Script Requirements

1. **Tone:** {config.voiceover.tone}
   - NOT a sales pitch - this is a technical showcase
   - Educational and confident, explaining HOW things work
   - Enthusiastic about the innovation

2. **Pacing:** {config.voiceover.pacing_wpm} words per minute
   - Each scene MUST fit within its allocated duration
   - Leave room for pauses and emphasis on technical terms

3. **Gemini 3 Mentions:** 
   - Mention "Gemini 3" or "Gemini 3 API" at least 2-3 times
   - Explain specifically HOW Gemini is used (not just that it is used)
   - Example: "Gemini 3 analyzes the product details and generates contextual scripts..."

4. **Technical Depth:**
   - Do NOT use vague marketing speak
   - BE SPECIFIC about architecture, APIs, and technical workflow
   - Example: Good ✅ "Gemini 3 API generates 3-5 script variants by analyzing audience demographics"
   - Example: Bad ❌ "AI creates amazing content"

5. **Data-Driven:**
   - Include specific metrics where available (cost savings, time reduction, market size)
   - Use concrete numbers to demonstrate impact

6. **Formatting:**
   - Output as Markdown with ## Scene N headings
   - Include narration beneath each heading
   - Add [PAUSE] markers where visual demonstrations need time
   - Add **bold** for key terms to emphasize during recording

---

# Output Format

```markdown
## Scene 1: [Scene Name]
**Duration Target: [X] seconds | Estimated Word Count: [Y] words**

[Narration text here with **key terms** bolded and [PAUSE] markers where needed]

---

## Scene 2: [Scene Name]
...
```

---

Now, generate the complete voiceover script optimized for maximum judging score. Remember: this is a technical demonstration, not a sales video. Focus on showcasing the engineering quality and Gemini 3 integration depth.
"""
    
    return prompt


def generate_voiceover_script(config: DemoConfig, output_path: str = "../OUTPUT/scripts/voiceover_script.md") -> str:
    """
    Generate voiceover script using Gemini API
    
    Args:
        config: DemoConfig object from config_loader
        output_path: Where to save the generated script
        
    Returns:
        Path to generated script file
    """
    
    # Configure Gemini API
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    # Initialize client with new SDK
    client = genai.Client(api_key=api_key)
    
    # Build prompt
    prompt = build_prompt_for_script_generation(config)
    
    print("🤖 Generating voiceover script with Gemini API...")
    print(f"   Product: {config.product.name}")
    print(f"   Total Scenes: {len(config.demo.scenes)}")
    print(f"   Target Duration: {config.demo.duration_seconds}s")
    print()
    
    # Generate script using gemini-2.5-flash (text model, working in project)
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,  # Balanced creativity
                top_p=0.9,
                top_k=40,
                max_output_tokens=4096,
            )
        )
        
        script_content = response.text
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    
    # Add metadata header
    script_with_metadata = f"""# Voiceover Script: {config.product.name}

**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Target Duration:** {config.demo.duration_seconds} seconds  
**Voice:** {config.voiceover.voice_id}  
**Pacing:** {config.voiceover.pacing_wpm} WPM  
**Tone:** {config.voiceover.tone}

---

{script_content}

---

## Production Notes

- Review timing for each scene (read aloud to verify)
- Adjust pacing if any scene exceeds allocated duration
- Emphasize **bolded terms** during voiceover recording
- Respect [PAUSE] markers for visual demonstrations
- Ensure Gemini 3 is mentioned prominently (target: 2-3 times)
"""
    
    # Save to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(script_with_metadata, encoding='utf-8')
    
    print(f"✅ Script generated successfully!")
    print(f"   Saved to: {output_file}")
    print(f"   Length: {len(script_content.split())} words")
    print(f"   Estimated duration: {len(script_content.split()) / config.voiceover.pacing_wpm:.1f} minutes")
    print()
    
    return str(output_file)


def validate_script_timing(script_path: str, config: DemoConfig) -> Dict[str, dict]:
    """
    Validate that script fits within scene duration constraints
    
    Returns dict of {scene_name: {estimated_seconds, allocated_seconds, status}}
    """
    
    script_content = Path(script_path).read_text(encoding='utf-8')
    
    # Extract scene sections
    import re
    scene_pattern = r'##\s+Scene\s+\d+:\s+(.*?)\n(.*?)(?=##\s+Scene\s+\d+:|\Z)'
    matches = re.finditer(scene_pattern, script_content, re.DOTALL)
    
    results = {}
    total_estimated_seconds = 0
    
    for match in matches:
        scene_name = match.group(1).strip()
        scene_text = match.group(2).strip()
        
        # Count words (excluding markdown formatting)
        words = re.findall(r'\b\w+\b', scene_text)
        word_count = len(words)
        
        # Estimate duration (WPM to seconds)
        estimated_seconds = (word_count / config.voiceover.pacing_wpm) * 60
        
        # Find matching scene in config
        matching_scene = next((s for s in config.demo.scenes if scene_name.lower() in s.name.lower()), None)
        
        if matching_scene:
            allocated_seconds = matching_scene.duration_seconds
            status = "✅ OK" if estimated_seconds <= allocated_seconds else "⚠️ TOO LONG"
            
            results[scene_name] = {
                "estimated_seconds": round(estimated_seconds, 1),
                "allocated_seconds": allocated_seconds,
                "word_count": word_count,
                "status": status,
                "overage": round(estimated_seconds - allocated_seconds, 1) if estimated_seconds > allocated_seconds else 0
            }
            
            total_estimated_seconds += estimated_seconds
    
    # Add total
    results["TOTAL"] = {
        "estimated_seconds": round(total_estimated_seconds, 1),
        "allocated_seconds": config.demo.duration_seconds,
        "status": "✅ OK" if total_estimated_seconds <= config.demo.duration_seconds else "⚠️ TOO LONG",
        "overage": round(total_estimated_seconds - config.demo.duration_seconds, 1) if total_estimated_seconds > config.demo.duration_seconds else 0
    }
    
    return results


def print_timing_report(timing_results: Dict[str, dict]):
    """Print formatted timing validation report"""
    
    print("\n" + "="*70)
    print("⏱️  SCRIPT TIMING VALIDATION REPORT")
    print("="*70)
    
    for scene_name, data in timing_results.items():
        if scene_name == "TOTAL":
            print("-" * 70)
        
        print(f"\n{scene_name}")
        print(f"  Estimated: {data['estimated_seconds']}s / Allocated: {data['allocated_seconds']}s")
        
        if 'word_count' in data:
            print(f"  Word Count: {data['word_count']}")
        
        print(f"  Status: {data['status']}")
        
        if data['overage'] > 0:
            print(f"  ⚠️  OVERAGE: {data['overage']}s - Script needs trimming!")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    import sys
    
    # Allow custom config path
    config_path = sys.argv[1] if len(sys.argv) > 1 else "../INPUT/configuration/Product_Specs.md"
    
    try:
        # Load configuration
        config = load_config(config_path)
        
        # Generate script
        script_path = generate_voiceover_script(config)
        
        # Validate timing
        timing_results = validate_script_timing(script_path, config)
        print_timing_report(timing_results)
        
        # Warn if script is too long
        if timing_results["TOTAL"]["status"] != "✅ OK":
            print("\n⚠️  WARNING: Script exceeds target duration!")
            print("   Consider:")
            print("   1. Re-running generation with stricter duration constraints")
            print("   2. Manually editing script to trim verbose sections")
            print("   3. Increasing pacing WPM slightly (current: {})".format(config.voiceover.pacing_wpm))
        else:
            print("\n✅ Script timing validated - ready for voiceover generation!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
