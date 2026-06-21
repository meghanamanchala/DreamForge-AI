import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY", "")

client = genai.Client(api_key=api_key)

models_to_test = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-flash-latest"]

for m in models_to_test:
    try:
        print(f"Testing model: {m}")
        response = client.models.generate_content(
            model=m,
            contents="Say hello"
        )
        print(f"Success {m}: {response.text}")
    except Exception as e:
        print(f"Failed {m}: {e}")
