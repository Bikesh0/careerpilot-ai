from app.ai.llm import LocalLLM

llm = LocalLLM()

print(
    llm.ask(
        "In two sentences, explain what a SOC Analyst does."
    )
)