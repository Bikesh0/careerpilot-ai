import ollama


class AIEngine:

    def __init__(
        self,
        model="llama3.1",
        keep_alive="30m",
    ):
        self.model = model
        self.keep_alive = keep_alive

    def ask(
        self,
        system_prompt,
        user_prompt,
    ):

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            keep_alive=self.keep_alive,
        )

        return response["message"]["content"]