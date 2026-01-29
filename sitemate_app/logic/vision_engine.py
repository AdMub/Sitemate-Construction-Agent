import google.generativeai as genai
import streamlit as st
from PIL import Image
import io
import time
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

def analyze_site_progress(image_bytes):
    """
    Sends the image to Google Gemini.
    Implements a 'Self-Healing' mechanism to try multiple models if one fails.
    """
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        return "❌ Error: GOOGLE_API_KEY not found in secrets.toml."

    # 1. Configure API
    genai.configure(api_key=api_key)

    # 2. List of models to try (Priority Order)
    # We prioritize 1.5-flash because it has the highest free limits.
    models_to_try = [
        'gemini-1.5-flash',       # Best for speed & free tier limits
        'gemini-1.5-pro',         # High intelligence
        'gemini-2.0-flash',       # Experimental (Low limits)
        'gemini-pro-vision'       # Legacy backup
    ]

    # 3. Process Image
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return f"❌ Image Error: Could not process the uploaded file. {str(e)}"

    # 4. The Vision Prompt
    prompt = """
    You are a Construction Site Surveyor. Analyze this image professionally.
    1. IDENTIFY: What stage of construction is this? (e.g., Foundation, Lintel, Roofing).
    2. COUNT: Estimate the visible number of blocks laid (rough count).
    3. PROGRESS: Estimate the percentage completion of the current stage (0-100%).
    4. OBSERVATION: Mention 1 safety or quality observation.
    
    Output format:
    **Stage:** [Stage Name]
    **Progress:** [XX]%
    **Observation:** [Brief text]
    """

    # 5. Try Models Loop
    last_error = ""
    
    for model_name in models_to_try:
        try:
            # Attempt to create model and generate content
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([prompt, image])
            
            # If successful, return immediately
            if response.text:
                return response.text
                
        except Exception as e:
            error_str = str(e)
            last_error = error_str
            
            # If Rate Limit (429), wait briefly and try next model
            if "429" in error_str:
                time.sleep(1) # Small cool-down
                continue 
            # If Model Not Found (404), try next model
            elif "404" in error_str or "not found" in error_str:
                continue
            # For other errors, keep trying next models just in case
            continue

    # 6. If all models fail
    return f"❌ Analysis Failed. All AI models are currently busy or unreachable.\nDetails: {last_error}"