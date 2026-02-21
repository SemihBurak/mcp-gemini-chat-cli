from google import genai
from google.genai import types


class Gemini:
    def __init__(self, model: str, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def chat(
        self,
        contents,
        system=None,
        tools=None,
        temperature=1.0,
    ):
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=8000,
        )
        if system:
            config.system_instruction = system
        if tools:
            config.tools = tools

        return self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

    @staticmethod
    def extract_text(response) -> str:
        """Extract text from a Gemini response."""
        try:
            return response.text
        except ValueError:
            return ""

    @staticmethod
    def has_function_calls(response) -> bool:
        """Check if the response contains any function calls."""
        if not response.candidates:
            return False
        for part in response.candidates[0].content.parts:
            if part.function_call:
                return True
        return False

    @staticmethod
    def get_function_calls(response) -> list[dict]:
        """Extract function calls from a Gemini response."""
        calls = []
        if not response.candidates:
            return calls
        for part in response.candidates[0].content.parts:
            if part.function_call:
                calls.append(
                    {
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args)
                        if part.function_call.args
                        else {},
                    }
                )
        return calls

    @staticmethod
    def get_model_content(response):
        """Get the model's response content for conversation history."""
        return response.candidates[0].content

    @staticmethod
    def make_function_responses(function_responses: list[dict]):
        """Create content with function responses.

        function_responses: list of {"name": str, "response": dict}
        """
        parts = [
            types.Part.from_function_response(
                name=fr["name"],
                response=fr["response"],
            )
            for fr in function_responses
        ]
        return types.Content(role="user", parts=parts)
