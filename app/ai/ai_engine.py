import os
import threading

import ollama


class AIEngine:
    """
    Thin Ollama wrapper used by the resume/cover-letter/profile
    generators.

    ask() previously called the bare ollama.chat() module function
    with no timeout. If Ollama is unreachable in a way that hangs
    rather than immediately refuses the connection (as opposed to
    "connection refused", which fails fast), that call could block a
    Flask request indefinitely. This mirrors the bounded, fail-soft
    design already used by app.ai.llm.LocalLLM: a hard timeout
    enforced from a daemon thread, returning None instead of hanging
    or raising when the model is unavailable.
    """

    def __init__(
        self,
        model="llama3.1",
        keep_alive="30m",
        timeout=None,
    ):
        self.model = model
        self.keep_alive = keep_alive

        self.timeout = int(
            timeout
            or os.getenv(
                "OLLAMA_TIMEOUT",
                30,
            )
        )

        self.client = ollama.Client(
            timeout=self.timeout
        )

    def ask(
        self,
        system_prompt,
        user_prompt,
    ):
        result = {
            "response": None,
            "error": None,
        }

        def worker():

            try:

                result["response"] = self.client.chat(
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

            except Exception as error:

                result["error"] = error

        thread = threading.Thread(
            target=worker,
            daemon=True,
        )

        thread.start()

        thread.join(
            timeout=self.timeout
        )

        if thread.is_alive():

            print(
                f"WARNING: AIEngine request timed out after "
                f"{self.timeout} seconds."
            )

            return None

        if result["error"] is not None:

            print(
                "WARNING: AIEngine request failed:",
                result["error"],
            )

            return None

        response = result["response"]

        if not response:
            return None

        return response["message"]["content"]