import json
from pathlib import Path


class MetadataStore:
    def __init__(self, path: str = ".metadata_store.json"):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        if not self.path.exists():
            return {
                "usage_count": 0,
                "feedback": [],
                "analytics": {
                    "queries_per_day": {},
                    "no_answer_rate": 0.0,
                    "helpfulness_score": 0.0,
                },
            }
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def record_query(self, query_text: str, result_status: str):
        self.data["usage_count"] += 1
        day = "today"
        self.data["analytics"]["queries_per_day"].setdefault(day, 0)
        self.data["analytics"]["queries_per_day"][day] += 1
        if result_status == "unsupported":
            # simple operational metric for the demo
            self.data["analytics"]["no_answer_rate"] = round(
                (self.data["analytics"]["no_answer_rate"] * (self.data["usage_count"] - 1) + 1.0)
                / self.data["usage_count"],
                3,
            )
        self.save()

    def record_feedback(self, rating: str):
        self.data["feedback"].append({"rating": rating})
        self.data["analytics"]["helpfulness_score"] = round(
            (sum(1 for item in self.data["feedback"] if item["rating"] == "helpful") /
             max(len(self.data["feedback"]), 1)) * 100,
            2,
        )
        self.save()
