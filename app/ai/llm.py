import os
import threading

import ollama


class LocalLLM:
    """
    Stable local Ollama interface for CareerPilot AI v2.0.

    Design goals:
    - Use local Ollama only.
    - Automatically detect an installed model.
    - Never allow an AI request to block CareerPilot indefinitely.
    - Limit generated output so daily analysis remains fast.
    - Fail gracefully when Ollama is unavailable.
    - Return None on failure so the rest of CareerPilot can continue.
    """

    def __init__(
        self,
        host=None,
        model=None,
        timeout=30,
        max_output_tokens=350,
    ):
        self.host = (
            host
            or os.getenv(
                "OLLAMA_HOST",
                "http://127.0.0.1:11434",
            )
        )

        self.timeout = int(
            os.getenv(
                "OLLAMA_TIMEOUT",
                timeout,
            )
        )

        self.max_output_tokens = int(
            os.getenv(
                "OLLAMA_MAX_TOKENS",
                max_output_tokens,
            )
        )

        self.model = (
            model
            or os.getenv(
                "OLLAMA_MODEL",
                "",
            )
        )

        self.client = ollama.Client(
            host=self.host,
            timeout=self.timeout,
        )

        self.available = False

        self._initialize_model()

    # =========================================================
    # Ollama initialization
    # =========================================================

    def _initialize_model(self):
        """
        Check Ollama and automatically select a local model.

        If OLLAMA_MODEL is configured, that model is preferred.
        Otherwise the first locally installed model is selected.
        """

        try:
            response = self.client.list()

            models = []

            if isinstance(response, dict):
                models = response.get(
                    "models",
                    [],
                )

            else:
                models = getattr(
                    response,
                    "models",
                    [],
                )

            if not models:

                print(
                    "WARNING: Ollama is running but no local models were found."
                )

                print(
                    "Install a model with:"
                )

                print(
                    "  ollama pull llama3.1"
                )

                self.available = False
                return

            # -------------------------------------------------
            # If no model was explicitly configured, select the
            # first installed local model.
            # -------------------------------------------------

            if not self.model:

                first_model = models[0]

                if isinstance(
                    first_model,
                    dict,
                ):

                    self.model = (
                        first_model.get("name")
                        or first_model.get("model")
                    )

                else:

                    self.model = (
                        getattr(
                            first_model,
                            "model",
                            None,
                        )
                        or getattr(
                            first_model,
                            "name",
                            None,
                        )
                        or str(first_model)
                    )

            self.available = bool(
                self.model
            )

            if self.available:

                print(
                    f"Local LLM: {self.model}"
                )

        except Exception as error:

            print(
                "WARNING: Ollama unavailable:",
                error,
            )

            self.available = False

    # =========================================================
    # Internal Ollama request
    # =========================================================

    def _chat(self, prompt):
        """
        Perform the actual Ollama request.

        This method is executed in a daemon thread by ask().
        """

        return self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            options={
                # Keep generation reasonably fast.
                "num_predict": self.max_output_tokens,

                # Low temperature gives more predictable job analysis.
                "temperature": 0.2,
            },
        )

    # =========================================================
    # Ask
    # =========================================================

    def ask(
        self,
        prompt,
    ):
        """
        Send a prompt to Ollama safely.

        Returns:
            str | None

        Important:
        CareerPilot must never depend on the LLM being available.
        A timeout or Ollama failure therefore returns None instead
        of crashing the complete daily job agent.
        """

        if not self.available:
            return None

        if not prompt:
            return None

        result = {
            "response": None,
            "error": None,
        }

        # -----------------------------------------------------
        # Run Ollama in a daemon thread.
        #
        # This prevents a slow Ollama request from blocking the
        # complete CareerPilot process forever.
        # -----------------------------------------------------

        def worker():

            try:

                result["response"] = self._chat(
                    prompt
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

        # -----------------------------------------------------
        # Hard application-level timeout.
        # -----------------------------------------------------

        if thread.is_alive():

            print(
                f"WARNING: Local LLM timed out after "
                f"{self.timeout} seconds."
            )

            print(
                "Continuing without AI analysis."
            )

            return None

        # -----------------------------------------------------
        # Request-level exception.
        # -----------------------------------------------------

        if result["error"] is not None:

            print(
                "WARNING: Local LLM request failed:",
                result["error"],
            )

            return None

        response = result["response"]

        if not response:
            return None

        # -----------------------------------------------------
        # Handle both dictionary-style and Ollama response
        # objects.
        # -----------------------------------------------------

        if isinstance(
            response,
            dict,
        ):

            message = response.get(
                "message",
                {},
            )

            if isinstance(
                message,
                dict,
            ):

                content = message.get(
                    "content",
                    "",
                )

            else:

                content = getattr(
                    message,
                    "content",
                    "",
                )

        else:

            message = getattr(
                response,
                "message",
                None,
            )

            if message is None:
                return None

            content = getattr(
                message,
                "content",
                "",
            )

        if not content:
            return None

        return str(
            content
        ).strip()

    # =========================================================
    # Status
    # =========================================================

    def status(self):
        """
        Return a simple status dictionary useful for diagnostics.
        """

        return {
            "available": self.available,
            "model": self.model,
            "host": self.host,
            "timeout": self.timeout,
            "max_output_tokens": self.max_output_tokens,
        }