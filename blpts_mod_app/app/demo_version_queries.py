"""Run the four version-scoped retrieval queries for the modernization demo."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from knowledge_assistant.core import KnowledgeAssistant


QUERIES = [
    ("Legacy only", "Why did type C renewals get charged different fees?", "legacy"),
    ("Legacy only", "Does the multi-year renewal discount apply to type C licenses?", "legacy"),
    ("Modernized only", "Does the multi-year renewal discount apply to type C licenses?", "mod_v1"),
    ("Compare both", "What changed about license renewal between the legacy and modernized systems?", "compare"),
]


if __name__ == "__main__":
    assistant = KnowledgeAssistant()
    for label, query, scope in QUERIES:
        answer = assistant.answer_question(query, scope)
        print(f"[{label}] {query}\n{answer['status']}: {answer['summary']}\n")