from google import genai
from google.genai import types
import json
import time

class BaseAgent:
    def __init__(self, client, model="gemini-3.1-flash-lite"):
        """
        Base agent class.
        :param client: An initialized google-genai Client instance.
        :param model: The Gemini model name (e.g., 'gemini-3.1-flash-lite' or 'gemini-2.5-flash').
        """
        self.client = client
        self.model = model
        self.last_tokens_used = 0
        self.last_latency_ms = 0

    def _execute_with_retry(self, contents, config):
        """Helper to invoke Gemini API with automatic retry backoffs for 429 and 503 errors."""
        max_retries = 6
        base_delay = 8.0

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config
                )
                return response
            except Exception as e:
                err_msg = str(e).lower()
                is_rate_limit = "429" in err_msg or "resource_exhausted" in err_msg or "quota" in err_msg
                is_unavailable = "503" in err_msg or "unavailable" in err_msg or "high demand" in err_msg or "try again" in err_msg

                if (is_rate_limit or is_unavailable) and attempt < max_retries - 1:
                    # 503 needs longer waits since the server needs time to recover
                    delay_multiplier = 2.0 if is_unavailable else 1.5
                    sleep_time = base_delay * (delay_multiplier ** attempt)
                    error_type = "503 UNAVAILABLE" if is_unavailable else "429 RATE LIMIT"
                    print(f"[{error_type}] Retrying in {sleep_time:.1f}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(sleep_time)
                else:
                    raise e

    def generate_text(self, system_instruction, user_content):
        """Generates standard unstructured text response."""
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )
            start_time = time.time()
            response = self._execute_with_retry(
                contents=user_content,
                config=config
            )
            self.last_latency_ms = int((time.time() - start_time) * 1000)
            self.last_tokens_used = response.usage_metadata.total_token_count if response.usage_metadata else 0
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
            start_time = time.time()
            response = self._execute_with_retry(
                contents=user_content,
                config=config
            )
            self.last_latency_ms = int((time.time() - start_time) * 1000)
            self.last_tokens_used = response.usage_metadata.total_token_count if response.usage_metadata else 0
            
            # The output should be valid JSON matching the schema
            return json.loads(response.text)
        except Exception as e:
            raise RuntimeError(f"Error in Gemini structured generation: {e}")

    def generate_text_with_tools(self, system_instruction, user_content, tools_list, tools_map):
        """
        Executes a loop to support native Gemini function calling.
        :param tools_list: List of Python functions.
        :param tools_map: Dictionary mapping function name -> function reference.
        """
        try:
            self.last_tokens_used = 0
            self.last_latency_ms = 0
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools_list,
                temperature=0.7
            )
            
            # We start a conversation history
            contents = [user_content]
            
            while True:
                start_time = time.time()
                response = self._execute_with_retry(
                    contents=contents,
                    config=config
                )
                self.last_latency_ms += int((time.time() - start_time) * 1000)
                if response.usage_metadata:
                    self.last_tokens_used += response.usage_metadata.total_token_count
                
                # Check if Gemini returned a function call
                if response.function_calls:
                    # We need to add the model's message (containing the function calls) to the history
                    contents.append(response.candidates[0].content)
                    
                    # Execute each function call and append the results as ToolResponse
                    tool_responses = []
                    for call in response.function_calls:
                        print(f"[NATIVE TOOL CALL] Executing tool: {call.name} with args {call.args}")
                        
                        if call.name in tools_map:
                            try:
                                # Convert args to standard dict
                                args_dict = dict(call.args)
                                result = tools_map[call.name](**args_dict)
                                # Format tool response
                                tool_responses.append(
                                    types.Part.from_function_response(
                                        name=call.name,
                                        response={"result": result}
                                    )
                                )
                            except Exception as e:
                                tool_responses.append(
                                    types.Part.from_function_response(
                                        name=call.name,
                                        response={"error": str(e)}
                                    )
                                )
                        else:
                            tool_responses.append(
                                types.Part.from_function_response(
                                    name=call.name,
                                    response={"error": f"Tool '{call.name}' not found."}
                                )
                            )
                    
                    # Append the function responses as a User content block
                    contents.append(types.Content(role="user", parts=tool_responses))
                else:
                    # Final output text received (no more tool calls)
                    return response
        except Exception as e:
            raise RuntimeError(f"Error in Gemini native tool generation: {e}")
