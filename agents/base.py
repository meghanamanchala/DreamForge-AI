from google import genai
from google.genai import types
import json

class BaseAgent:
    def __init__(self, client, model="gemini-2.5-flash"):
        """
        Base agent class.
        :param client: An initialized google-genai Client instance.
        :param model: The Gemini model name (e.g., 'gemini-2.5-flash' or 'gemini-2.5-pro').
        """
        self.client = client
        self.model = model

    def generate_text(self, system_instruction, user_content):
        """Generates standard unstructured text response."""
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_content,
                config=config
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Error in Gemini text generation: {e}")

    def generate_structured(self, system_instruction, user_content, response_schema):
        """
        Generates structured JSON output conforming to a Pydantic schema.
        :param response_schema: Pydantic class defining the target schema.
        """
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.2, # Lower temperature for structured extraction accuracy
            )
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_content,
                config=config
            )
            
            # The output should be valid JSON matching the schema
            return json.loads(response.text)
        except Exception as e:
            raise RuntimeError(f"Error in Gemini structured generation: {e}")
