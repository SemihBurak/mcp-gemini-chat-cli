from core.gemini import Gemini
from mcp_client import MCPClient
from core.tools import ToolManager


class Chat:
    def __init__(self, gemini_service: Gemini, clients: dict[str, MCPClient]):
        self.gemini_service: Gemini = gemini_service
        self.clients: dict[str, MCPClient] = clients
        self.contents: list = []

    async def _process_query(self, query: str):
        self.contents.append({"role": "user", "parts": [{"text": query}]})

    async def run(
        self,
        query: str,
    ) -> str:
        await self._process_query(query)

        while True:
            tools = await ToolManager.get_all_tools(self.clients)

            response = self.gemini_service.chat(
                contents=self.contents,
                tools=tools if tools else None,
            )

            # Add model response to conversation history
            self.contents.append(
                self.gemini_service.get_model_content(response)
            )

            if self.gemini_service.has_function_calls(response):
                text = self.gemini_service.extract_text(response)
                if text:
                    print(text)

                function_calls = self.gemini_service.get_function_calls(
                    response
                )
                function_responses = await ToolManager.execute_tool_requests(
                    self.clients, function_calls
                )

                self.contents.append(
                    self.gemini_service.make_function_responses(
                        function_responses
                    )
                )
            else:
                return self.gemini_service.extract_text(response)
