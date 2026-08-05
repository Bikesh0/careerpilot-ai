from ollama import chat


class LocalLLM:

    def __init__(self, model="llama3.1"):
        self.model = model

    def ask(self, prompt):

        response = chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]