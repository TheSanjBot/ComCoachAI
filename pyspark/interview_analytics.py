from __future__ import annotations

"""Lightweight Stage 13 interview analytics over generated report artifacts."""

from datetime import datetime
import json
from pathlib import Path
from typing import Any


def _load_rows(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if source.is_file():
        payload = json.loads(source.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else [payload]

    rows: list[dict[str, Any]] = []
    for artifact in source.rglob("*.json"):
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            rows.extend(item for item in payload if isinstance(item, dict))
        elif isinstance(payload, dict):
            rows.append(payload)
    return rows


def build_interview_analytics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    filtered = [row for row in rows if row.get("mode") == "Interview Training Mode"]
    if not filtered:
        return {
            "average_technical_score": 0.0,
            "common_weak_skills": [],
            "difficult_topics": [],
            "history": [],
        }

    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F

        spark = SparkSession.builder.master("local[*]").appName("commcoach-interview-analytics").getOrCreate()
        frame = spark.createDataFrame(filtered)
        average_technical_score = float(
            frame.agg(F.round(F.avg("technical_score"), 2).alias("average_technical_score")).collect()[0][
                "average_technical_score"
            ]
            or 0.0
        )

        weak_skills = (
            frame.select(F.explode_outer("weaknesses").alias("weakness"))
            .groupBy("weakness")
            .count()
            .orderBy(F.desc("count"))
            .limit(5)
            .collect()
        )
        difficult_topics = (
            frame.select(F.explode_outer(F.col("analytics.weakest_topics")).alias("topic"))
            .groupBy("topic")
            .count()
            .orderBy(F.desc("count"))
            .limit(5)
            .collect()
        )
        history = (
            frame.select("title", "role", "technical_score", "communication_score", "created_at")
            .orderBy(F.desc("created_at"))
            .limit(5)
            .collect()
        )
        spark.stop()
        return {
            "average_technical_score": average_technical_score,
            "common_weak_skills": [row["weakness"] for row in weak_skills if row["weakness"]],
            "difficult_topics": [row["topic"] for row in difficult_topics if row["topic"]],
            "history": [
                {
                    "title": row["title"],
                    "role": row["role"],
                    "technical_score": row["technical_score"],
                    "communication_score": row["communication_score"],
                    "created_at": row["created_at"],
                }
                for row in history
            ],
        }
    except Exception:
        ordered = sorted(
            filtered,
            key=lambda row: datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00")),
            reverse=True,
        )
        weak_skill_counts: dict[str, int] = {}
        topic_counts: dict[str, int] = {}
        for row in filtered:
            for weakness in row.get("weaknesses", []) or []:
                weak_skill_counts[weakness] = weak_skill_counts.get(weakness, 0) + 1
            for topic in (row.get("analytics") or {}).get("weakest_topics", []) or []:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        return {
            "average_technical_score": round(
                sum(float(row.get("technical_score", 0) or 0) for row in filtered) / len(filtered),
                2,
            ),
            "common_weak_skills": [
                item[0]
                for item in sorted(weak_skill_counts.items(), key=lambda pair: pair[1], reverse=True)[:5]
            ],
            "difficult_topics": [
                item[0]
                for item in sorted(topic_counts.items(), key=lambda pair: pair[1], reverse=True)[:5]
            ],
            "history": [
                {
                    "title": row.get("title"),
                    "role": row.get("role"),
                    "technical_score": row.get("technical_score"),
                    "communication_score": row.get("communication_score"),
                    "created_at": row.get("created_at"),
                }
                for row in ordered[:5]
            ],
        }


def main(source_path: str = "reports/final") -> None:
    print(json.dumps(build_interview_analytics(_load_rows(source_path)), indent=2))


if __name__ == "__main__":
    main()
