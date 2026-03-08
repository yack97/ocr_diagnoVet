import os
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "immersion-005-7e407"
LOCATIONS = ["us-central1", "europe-west1", "europe-west4", "europe-west3"]
MODELS = ["gemini-1.5-flash-001", "gemini-1.5-flash", "gemini-1.0-pro", "gemini-1.5-pro", "gemini-1.5-flash-002"]

print("Starting Vertex AI tests...")

for loc in LOCATIONS:
    print(f"\nTesting location: {loc}")
    vertexai.init(project=PROJECT_ID, location=loc)
    
    for mod in MODELS:
        try:
            model = GenerativeModel(mod)
            # A simple lightweight call to test if the model endpoint is accessible
            resp = model.generate_content("hello")
            print(f"✅ SUCCESS: {mod} in {loc} (Response: {resp.text.strip()})")
            
            # If we find one that works, exit
            import sys
            sys.exit(0)
            
        except Exception as e:
            err_msg = str(e).split('\n')[0] # Get first line of error
            print(f"❌ FAIL: {mod} in {loc} -> {err_msg}")
