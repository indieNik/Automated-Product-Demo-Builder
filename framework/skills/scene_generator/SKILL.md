---
name: Scene Generator
description: Generates AI-powered visual scenes (hooks, tech stacks) for product demos using Gemini models.
---

# Scene Generator Skill

## Overview
This skill generates professional visual assets for the demo video, specifically:
- **Hook Scene**: An attention-grabbing opening visual representing the problem statement.
- **Tech Wrap-up Scene**: A professional showcase of the technology stack used.

## Usage
```python
from skills.scene_generator.agent import GeminiSceneGenerator

generator = GeminiSceneGenerator(api_key="...")
path, script = generator.generate_hook_scene(problem="...", hook="...", output_path=...)
```

## Dependencies
- `google-genai`
- `Pillow`
