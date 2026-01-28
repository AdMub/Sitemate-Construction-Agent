### (This handles the JSON parsing and cleaning tools).

import re
import json

def extract_json_from_text(text):
    """Finds and parses JSON content between ||| pipes."""
    try:
        match = re.search(r'\|\|\|(.*?)\|\|\|', text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
    except:
        pass
    return None

def clean_ai_text(text):
    """Removes the JSON block from the text for display in the chat."""
    if text and "|||" in text:
        return text.split("|||")[0].replace("### JSON", "").strip()
    return text