import json


class JSONParser:

    @staticmethod
    def parse(text):

        try:
            return json.loads(text)

        except Exception:

            start = text.find("{")

            end = text.rfind("}")

            if start == -1 or end == -1:
                raise ValueError("No JSON found in AI response.")

            return json.loads(text[start:end + 1])