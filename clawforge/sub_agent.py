import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class SubAgent:
    def __init__(self, role: str, goal: str):
        self.role = role
        self.goal = goal

    def run(self, task: str, context: str = "") -> str:
        user_message = f"Task: {task}"
        if context:
            user_message += f"\n\nContext:\n{context}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are the {self.role}. Your job: {self.goal}"},
                {"role": "user",   "content": user_message},
            ],
        )
        return response.choices[0].message.content
