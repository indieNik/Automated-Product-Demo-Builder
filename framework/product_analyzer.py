#!/usr/bin/env python3
"""
Product Analysis Agent - Automated Product Demo Builder
"""
import os
import sys
import argparse
import time
import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
except ImportError:
    print("❌ Selenium not installed. Please run: pip install -r framework/requirements.txt")
    sys.exit(1)

# Gemini SDK
try:
    import google.genai as genai
    from dotenv import load_dotenv
except ImportError:
    print("⚠️  Google GenAI SDK or python-dotenv not installed.")
    sys.exit(1)

# Load environment variables
load_dotenv()

@dataclass
class ProductData:
    url: str
    name: Optional[str]
    screenshot_path: Optional[str] = None
    text_content: Optional[str] = None
    screenshot_path: Optional[str] = None
    text_content: Optional[str] = None
    interactive_elements: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None

class BrowserAnalyzer:
    def __init__(self, headless: bool = True):
        self.options = Options()
        if headless:
            self.options.add_argument("--headless=new")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        
    def analyze(self, url: str, product_name: Optional[str] = None) -> ProductData:
        print(f"🔍 Analyzing: {url}")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        product_data = ProductData(url=url, name=product_name)
        
        try:
            # Navigate
            driver.get(url)
            time.sleep(3)  # Wait for load
            
            # Screenshot
            screenshot_dir = Path("INPUT/raw_recordings")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = int(time.time())
            screenshot_path = screenshot_dir / f"analysis_screenshot_{timestamp}.png"
            
            # Set localized window size for realistic rendering (avoiding 100vh distortion)
            driver.set_window_size(1920, 1080)
            
            # 1. Scroll to bottom to trigger lazy loading
            total_height = driver.execute_script("return document.body.scrollHeight")
            current_scroll = 0
            while current_scroll < total_height:
                driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                time.sleep(0.5) # Wait for animations/load
                current_scroll += 1080
                total_height = driver.execute_script("return document.body.scrollHeight") # Re-check height
            
            # 2. Capture and stitch
            from PIL import Image
            import io
            
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            total_height = driver.execute_script("return document.body.scrollHeight")
            num_scrolls = int(total_height / 1080) + 1
            
            stitched_image = Image.new('RGB', (1920, total_height))
            
            for i in range(num_scrolls):
                scroll_y = min(i * 1080, total_height - 1080)
                if scroll_y < 0: scroll_y = 0
                
                driver.execute_script(f"window.scrollTo(0, {scroll_y});")
                time.sleep(0.5) # Stabilize
                
                
                # Capture viewport
                png_data = driver.get_screenshot_as_png()
                screenshot = Image.open(io.BytesIO(png_data))
                
                # Paste into stitched image
                # Logic: If we are at the very bottom, we might need to crop the top of the screenshot?
                # Simpler: Just paste at scroll_y. 
                # Note: 'scroll_y' is where the top of the viewport is.
                stitched_image.paste(screenshot, (0, scroll_y))
            
            stitched_image.save(str(screenshot_path))
            print(f"📸 Screenshot saved: {screenshot_path}")
            product_data.screenshot_path = str(screenshot_path)
            
            # Extract Text (Simple extraction for now)
            body_text = driver.find_element(By.TAG_NAME, "body").text
            product_data.text_content = body_text[:15000] # Limit to 15k chars
            print(f"📝 Extracted {len(product_data.text_content)} chars of text")
            
            # Extract Interactive Elements for Test Actions
            elements_info = []
            
            # Buttons and Links
            interactables = driver.find_elements(By.CSS_SELECTOR, "button, a, input, [role='button']")
            for i, el in enumerate(interactables[:50]): # Limit to top 50 relevant elements
                try:
                    if not el.is_displayed(): continue
                    tag = el.tag_name
                    text = el.text.strip().replace("\n", " ")[:50]
                    el_id = el.get_attribute("id")
                    el_class = el.get_attribute("class")
                    el_type = el.get_attribute("type")
                    
                    if not text and not el_id and not el.get_attribute("aria-label"):
                        continue
                        
                    desc = f"<{tag}"
                    if text: desc += f" text='{text}'"
                    if el_id: desc += f" id='{el_id}'"
                    if el_type: desc += f" type='{el_type}'"
                    desc += ">"
                    elements_info.append(desc)
                except:
                    continue
                    
            product_data.interactive_elements = "\n".join(elements_info)
            print(f"🖱️ Found {len(elements_info)} interactive elements")
            
        except Exception as e:
            print(f"❌ Browser analysis failed: {e}")
        finally:
            driver.quit()
            
        return product_data

class GeminiAnalyzer:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            sys.exit(1)
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash" # Using Flash for speed/multimodal

    def analyze_product(self, data: ProductData) -> Dict[str, Any]:
        print("🧠 Sending data to Gemini for analysis...")
        
        prompt = f"""
        Analyze this product website screenshot and text content to generate a comprehensive product specification for a demo video.
        
        Product URL: {data.url}
        Product Name (if known): {data.name if data.name else "Extract from content"}
        
        Website Text Content:
        {data.text_content}
        
        
        Interactive Elements Found on Page:
        {data.interactive_elements}
        
        You MUST return a JSON object with the following structure:
        {{
            "product_name": "Name of the product",
            "tagline": "A catchy, short tagline (max 10 words)",
            "category": "Product Category (e.g. SaaS, DevTool, E-commerce)",
            "problem_statement": "The core problem this product solves (max 300 chars)",
            "solution_overview": "How the product solves it (max 300 chars)",
            "key_features": ["Feature 1", "Feature 2", "Feature 3"],
            "target_audience": "Who this is for",
            "colors": {{
                "primary": "#HexCode",
                "background": "#HexCode",
                "accent": "#HexCode"
            }},
            "demo_scenes": [
                {{
                    "name": "Scene Name",
                    "objective": "What to demonstrate",
                    "visuals": "Description of visuals",
                    "actions": [
                        "Click button with text 'Login'",
                        "Type '{data.analysis_result.get('credentials', 'test@test.com') if data.analysis_result else 'test@test.com'}' in input with type 'email'",
                        "Wait 3 seconds"
                    ]
                }}
            ]
        }}
        
        IMPORTANT for "actions":
        - Use specific text or IDs from the 'Interactive Elements' list provided above.
        - Format actions clearly: "Click [Text]", "Type [Text] in [Element]", "Wait [Seconds]".
        - If credentials are required, use '{data.analysis_result.get('credentials', 'test@test.com') if data.analysis_result else 'test@test.com'}' (first part username, second password).
        """
        
        try:
            # Prepare contents
            contents = [prompt]
            if data.screenshot_path:
                from PIL import Image
                image = Image.open(data.screenshot_path)
                contents.append(image)
            
            # Retry loop for 429 errors
            max_retries = 3
            retry_delay = 5
            
            response = None
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config={
                            'response_mime_type': 'application/json'
                        }
                    )
                    break # Success
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
                        if attempt < max_retries - 1:
                            print(f"⚠️  Quota exceeded (429). Retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2 # Exponential backoff
                            continue
                    raise e # Re-raise if not a 429 or if max retries reached
            
            if not response:
                raise Exception("Failed to get response after retries")

            result = json.loads(response.text)
            print("✅ Gemini analysis complete")
            return result
            
        except Exception as e:
            print(f"❌ Gemini analysis failed: {e}")
            return {}

def update_product_specs(data: ProductData, analysis: Dict[str, Any], output_path: str):
    """Update the Product_Specs.json file with analyzed data"""
    path = Path(output_path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        
    # Construct JSON structure
    product_specs = {
        "product": {
            "name": analysis.get("product_name", "Unknown Product"),
            "tagline": analysis.get("tagline", ""),
            "url": data.url,
            "category": analysis.get("category", "SaaS"),
            "problem": analysis.get("problem_statement", ""),
            "solution": analysis.get("solution_overview", "")
        },
        "demo": {
            "duration_seconds": 180,
            "scenes": []
        },
        "judging_criteria": {
            "technical_execution": {
                "weight": 0.4,
                "strategies": ["Highlight backend logic"]
            },
             "potential_impact": {
                "weight": 0.2,
                "strategies": ["Focus on user productivity"]
            },
            "innovation": {
                "weight": 0.3,
                "strategies": ["Showcase unique AI features"]
            },
            "presentation": {
                "weight": 0.1,
                "strategies": ["Ensure smooth transitions"]
            }
        },
        "voiceover": {
            "voice_id": "EaBs7G1VibMrNAuz2Na7",
            "tone": "Confident, professional",
            "pacing_wpm": 145,
            "stability": 0.5,
            "clarity": 0.75,
            "style": 0.5
        },
        "assets": {
            "test_credentials": {}
        }
    }
    
    # Process Credentials
    creds = analysis.get('credentials', '')
    if creds:
        if '/' in creds:
            parts = creds.split('/')
            product_specs["assets"]["test_credentials"] = {"email": parts[0], "password": parts[1]}
        else:
            product_specs["assets"]["test_credentials"] = {"email": creds, "password": "password"}
            
    # Process Scenes
    raw_scenes = analysis.get('demo_scenes', [])
    start_time = 0
    
    for i, scene in enumerate(raw_scenes, 1):
        duration = 30 # Default 30s
        end_time = start_time + duration
        
        # Format MM:SS
        start_min, start_sec = divmod(start_time, 60)
        end_min, end_sec = divmod(end_time, 60)
        time_range = f"{start_min}:{start_sec:02d}-{end_min}:{end_sec:02d}"
        
        new_scene = {
            "name": f"Scene {i}: {scene.get('name', f'Scene {i}')}",
            "duration": time_range,
            "objective": scene.get('objective', ''),
            "visuals": scene.get('visuals', ''),
            "key_points": [],
            "actions": scene.get('actions', [])
        }
        
        # Add key features to first scene or where appropriate
        if i == 1 and analysis.get('key_features'):
             new_scene["key_points"] = analysis.get('key_features')
             
        product_specs["demo"]["scenes"].append(new_scene)
        start_time = end_time
        
    # Write JSON
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(product_specs, f, indent=2)
        
    print(f"✅ Updated {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Analyze product URL and generate Product_Specs.json")
    parser.add_argument("--url", required=True, help="Product URL to analyze")
    parser.add_argument("--name", help="Product Name (optional)")
    parser.add_argument("--credentials", help="Login credentials (email/password)")
    parser.add_argument("--output", default="../INPUT/configuration/Product_Specs.json", help="Output path for Product_Specs.json")
    
    args = parser.parse_args()
    
    # 1. Browser Analysis
    browser = BrowserAnalyzer()
    data = browser.analyze(args.url, args.name)
    
    # 2. Gemini Analysis
    gemini = GeminiAnalyzer()
    analysis_result = gemini.analyze_product(data)
    data.analysis_result = analysis_result
    
    # 3. Update Config
    if analysis_result:
        # Resolve output path relative to script if needed, or use absolute
        # If args.output starts with .., resolve it relative to __file__
        if args.output.startswith(".."):
            output_path = Path(__file__).parent / args.output
        else:
            output_path = Path(args.output)
            
        if args.output.startswith(".."):
            output_path = Path(__file__).parent / args.output
        else:
            output_path = Path(args.output)
            
        # Check if credentials provided
        if args.credentials:
             data.analysis_result["credentials"] = args.credentials
             
        update_product_specs(data, analysis_result, str(output_path))
    else:
        print("❌ Failed to generate analysis result.")

    
if __name__ == "__main__":
    main()
