import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class SubAgent:
    def __init__(self, role: str, goal: str, tools: list = None, tool_executor=None):
        self.role = role
        self.goal = goal
        self.tools = tools or []
        self.tool_executor = tool_executor  # comes from LangGraph

    def run(self, task: str, context: str = "") -> str:
        # Step 1: If tools exist, fetch information directly
        tool_data = self._run_tools(task)

        # Step 2: Pass fetched data + context to LLM for processing
        messages = self._build_messages(task, context, tool_data)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        return response.choices[0].message.content

    def _run_tools(self, task: str) -> str:
        if not self.tools or not self.tool_executor:
            return ""

        results = []
        for tool in self.tools:
            tool_name = tool["function"]["name"]
            result = self.tool_executor(tool_name, {"query": task})
            results.append(f"[{tool_name}]:\n{result}")

        return "\n\n".join(results)

    def _build_messages(self, task: str, context: str, tool_data: str) -> list:
        user_msg = f"Task: {task}"
        if context:
            user_msg += f"\n\nContext from previous agents:\n{context}"
        if tool_data:
            user_msg += f"\n\nData fetched by tools:\n{tool_data}"

        return [
            {"role": "system", "content": f"You are the {self.role}. Your job: {self.goal}"},
            {"role": "user",   "content": user_msg},
        ]
