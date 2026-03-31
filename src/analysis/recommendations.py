from __future__ import annotations

import json
import sqlite3
from pathlib import Path

RULES_PATH = Path(__file__).parent / "recommendation_rules.json"


class RecommendationEngine:
    def __init__(self, db_path: str, rules_path: Path = RULES_PATH):
        self.db_path = db_path
        with open(rules_path, encoding="utf-8") as f:
            self.rules: dict = json.load(f)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recommendation_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    anomaly_type TEXT NOT NULL,
                    atm_id TEXT,
                    vote TEXT NOT NULL CHECK(vote IN ('like','dislike')),
                    user_role TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            conn.commit()

    def get_adjusted_confidence(self, anomaly_type: str) -> float:
        rule = self.rules.get(anomaly_type)
        if not rule:
            return 0.5
        base: float = rule["confidence_base"]
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN vote = 'like' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN vote = 'dislike' THEN 1 ELSE 0 END)
                FROM recommendation_feedback
                WHERE anomaly_type = ?
                """,
                (anomaly_type,),
            ).fetchone()
        likes = row[0] or 0
        dislikes = row[1] or 0
        total = likes + dislikes
        if total == 0:
            return base
        # Laplace smoothing (denominator + 4) prevents extreme swings from sparse feedback
        ratio = (likes - dislikes) / (total + 4)
        return round(min(0.99, max(0.10, base + ratio * 0.15)), 2)

    def get_for_anomaly(self, anomaly_type: str, atm_id: str | None = None) -> dict | None:
        rule = self.rules.get(anomaly_type)
        if not rule:
            return None
        return {
            "anomaly_type": anomaly_type,
            "anomaly_name": rule["name"],
            "root_cause": rule["root_cause"],
            "steps": rule["steps"],
            "confidence": self.get_adjusted_confidence(anomaly_type),
            "explanation": rule["explanation"],
            "atm_id": atm_id,
        }

    def get_all_recommendations(self, detections: list[dict]) -> list[dict]:
        seen: set[tuple] = set()
        results: list[dict] = []
        for d in sorted(detections, key=lambda x: 0 if x.get("severity") == "CRITICAL" else 1):
            atype = d.get("anomaly_type")
            atm_id = d.get("atm_id")
            key = (atype, atm_id)
            if key in seen:
                continue
            seen.add(key)
            rec = self.get_for_anomaly(atype, atm_id)
            if rec:
                rec["severity"] = d.get("severity", "WARNING")
                rec["source"] = d.get("source", "")
                results.append(rec)
        results.sort(key=lambda r: r["confidence"], reverse=True)
        return results

    def record_feedback(
        self, anomaly_type: str, atm_id: str, vote: str, user_role: str | None = None
    ) -> bool:
        if vote not in ("like", "dislike"):
            return False
        if anomaly_type not in self.rules:
            return False
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO recommendation_feedback (anomaly_type, atm_id, vote, user_role)
                VALUES (?, ?, ?, ?)
                """,
                (anomaly_type, atm_id or "", vote, user_role),
            )
            conn.commit()
        return True

    def get_feedback_history(self, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT anomaly_type, atm_id, vote, user_role, created_at
                FROM recommendation_feedback
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "anomaly_type": r[0],
                "atm_id": r[1],
                "vote": r[2],
                "user_role": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]

    def get_feedback_stats(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    anomaly_type,
                    SUM(CASE WHEN vote = 'like' THEN 1 ELSE 0 END) AS likes,
                    SUM(CASE WHEN vote = 'dislike' THEN 1 ELSE 0 END) AS dislikes
                FROM recommendation_feedback
                GROUP BY anomaly_type
                """
            ).fetchall()
        return [
            {"anomaly_type": r[0], "likes": r[1] or 0, "dislikes": r[2] or 0}
            for r in rows
        ]
