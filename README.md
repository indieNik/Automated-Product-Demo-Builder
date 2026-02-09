# Product Demo Framework - Quick Start

## 🚀 Generate Your Demo Video in 4 Steps

### 1. Install Dependencies
```bash
cd PRODUCT_DEMO/framework
pip3 install -r requirements.txt
brew install ffmpeg  # macOS only
```

### 2. Set Environment Variables
Create `.env` in project root:
```bash
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key  
ELEVENLABS_API_KEY=your-key
```

### 3. Run Pipeline
```bash
cd framework
python3 orchestrator.py --config=../INPUT/configuration/Product_Specs.md
```

### 4. Manual Screen Recording
When prompted, record your screen:
- Use QuickTime: File → New Screen Recording
- Resolution: 1920x1080
- Save as: `../INPUT/raw_recordings/screen_recording.webm`

Then re-run with:
```bash
python3 orchestrator.py --recording=../INPUT/raw_recordings/screen_recording.webm
```

---

## 📖 Full Documentation

See [FRAMEWORK_GUIDE.md](./FRAMEWORK_GUIDE.md) for:
- Detailed usage instructions
- Customization options
- Troubleshooting guide
- Reusing for other products

---

## 🧪 Test Individual Components

```bash
# Test config parsing
python3 config_loader.py ../INPUT/configuration/Product_Specs.md

# Generate script only
python3 script_generator.py ../INPUT/configuration/Product_Specs.md

# Generate recording instructions
python3 recording_orchestrator.py ../INPUT/configuration/Product_Specs.md
```

---

**Framework Version:** 1.0.0  
**Created:** 2026-02-08
