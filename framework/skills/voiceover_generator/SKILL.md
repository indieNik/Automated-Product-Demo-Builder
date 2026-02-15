---
name: Voiceover Generator
description: Generates professional voiceovers from a storyline script using ElevenLabs.
---

# Voiceover Generator Skill

## Overview
This skill converts the text script from `Storyline.md` into high-quality audio files for each scene.

## Features
- Parses `Storyline.md` to extract per-scene scripts.
- Uses ElevenLabs API for neural voice synthesis.
- Supports emotion tags and pacing adjustments.

## Usage
```python
# Command line
python3 framework/skills/voiceover_generator/agent.py --storyline=... --output_dir=...
```

## Dependencies
- `elevenlabs`
- `python-dotenv`
