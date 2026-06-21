import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY", "")
print("API Key loaded, length:", len(api_key))

client = genai.Client(api_key=api_key)

print("Listing models:")
try:
    for m in client.models.list():
        print(m.name, m.supported_actions)
except Exception as e:
    print("Error listing models:", e)
