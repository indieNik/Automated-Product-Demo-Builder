# Automated Product Demo Builder - GEMINI.md

## 🌍 Project Overview
This project is a modular, config-driven framework for generating professional product demo videos. It automates script generation, voiceover synthesis, captioning, and video composition.

**Current Product Configuration:** [None - Ready for Configuration]

## 🛠 Tech Stack
- **Language:** Python 3
- **Core Libraries:** 
  - `google-generativeai` (Gemini API)
  - `elevenlabs` (Voiceover)
  - `Gemini Speech-to-Text` (Captions)
  - `ffmpeg-python` (Video Composition)
- **Infrastructure:** Local execution with API integrations.

## 📂 Key Directories & Files
- **/<PRODUCT_NAME>/**: Product-specific Runs
  - `run_<product>.log`: Execution logs.
  - `INPUT-<timestamp>/`: Input components to be read from `<Product_Name>/INPUT-<timestamp>/`
    - `configuration/Product_Specs.md`: Main configuration file.
    - `raw_recordings/`: Input screen recordings.
    - `assets/`: Static assets (logos, background music).
  - `OUTPUT-<timestamp>/`: Generated artifacts are now stored in `<Product_Name>/OUTPUT-<timestamp>/`.
    - `scripts/`: Generated voiceover scripts.
    - `scenes/`: AI generated scenes.
    - `voiceover/`: Generated audio.
    - `captions/`: Generated subtitles.
  - `final_video/`: Final output videos.
- **/framework/**: Core python logic.


## 🚀 Workflows
1.  **Configure:** Edit `<PRODUCT_NAME>/INPUT-<timestamp>/configuration/Product_Specs.md`.
2.  **Run Pipeline:** `python framework/orchestrator.py --config=<PRODUCT_NAME>/INPUT-<timestamp>/configuration/Product_Specs.md`
3.  **Manual Recording:** Record screen when prompted (if not fully automated).

## 🧠 Context
- The framework is designed to be reusable for different products by swapping the `Product_Specs.md`.
- Codebase follows a modular architecture where each step (script, voice, captions, video) can be run independently or orchestrated together.
- Aesthetics and "wow" factor are critical for the generated demos.

## 📝 Rules for AI
- Always check `<PRODUCT_NAME>/INPUT/configuration/Product_Specs.md` for current product context.
- When modifying framework code, ensure backward compatibility for other potential product configs.
- Prefer `pip3 install -r requirements.txt` for dependency management.
