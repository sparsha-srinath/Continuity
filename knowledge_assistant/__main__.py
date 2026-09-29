from .core import KnowledgeAssistant


if __name__ == "__main__":
    assistant = KnowledgeAssistant()
    print(assistant.answer_question("Why does the surcharge logic look inconsistent for accounts near 1000 kWh?"))
