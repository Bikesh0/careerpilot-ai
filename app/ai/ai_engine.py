import ollama


class AIEngine:

    def __init__(self, model="llama3.1"):

        self.model = model

    def ask(self, system_prompt, user_prompt):

        response = ollama.chat(

            model=self.model,

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content": user_prompt
                }

            ]

        )

        return response["message"]["content"]