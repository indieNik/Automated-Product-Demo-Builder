# Automated Product Demo Builder - GEMINI.md

## 🌍 Project Overview
This project is a modular, config-driven framework for generating professional product demo videos. It automates script generation, voiceover synthesis, captioning, and video composition.

**Current Product Configuration:** IgniteAI (Production-Grade Agentic UGC Video Factory)

## 🛠 Tech Stack
- **Language:** Python 3
- **Core Libraries:** 
  - `google-generativeai` (Gemini API)
  - `elevenlabs` (Voiceover)
  - `openai-whisper` (Captions)
  - `ffmpeg-python` (Video Composition)
- **Infrastructure:** Local execution with API integrations.

## 📂 Key Directories & Files
- **/INPUT/**: Input components.
  - `configuration/Product_Specs.md`: Main configuration file.
  - `raw_recordings/`: Input screen recordings.
  - `assets/`: Static assets (logos, background music).
- **/OUTPUT/**: Generated artifacts.
  - `scripts/`: Generated voiceover scripts.
  - `voiceover/`: Generated audio.
  - `captions/`: Generated subtitles.
  - `scenes/`: AI generated scenes.
  - `final_video/`: Final output videos.
- **/framework/**: Core python logic.


## 🚀 Workflows
1.  **Configure**: Edit `INPUT/configuration/Product_Specs.md`.
2.  **Run Pipeline**: `python framework/orchestrator.py --config=INPUT/configuration/Product_Specs.md`
3.  **Manual Recording**: Record screen when prompted (if not fully automated).

## 🧠 Context
- The framework is designed to be reusable for different products by swapping the `Product_Specs.md`.
- Codebase follows a modular architecture where each step (script, voice, captions, video) can be run independently or orchestrated together.
- Aesthetics and "wow" factor are critical for the generated demos.

## 📝 Rules for AI
- Always check `INPUT/configuration/Product_Specs.md` for current product context.
- When modifying framework code, ensure backward compatibility for other potential product configs.
- Prefer `pip install -r requirements.txt` for dependency management.
