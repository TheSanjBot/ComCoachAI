from __future__ import annotations

"""Lightweight Stage 13 communication analytics over generated report artifacts."""

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


def build_communication_trends(rows: list[dict[str, Any]]) -> dict[str, Any]:
    filtered = [
        row
        for row in rows
        if float(row.get("communication_score", 0) or 0) > 0
    ]
    if not filtered:
        return {
            "average_words_per_minute": 0.0,
            "average_filler_words": 0.0,
            "average_communication_score": 0.0,
            "trend_points": [],
        }

    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F

        spark = SparkSession.builder.master("local[*]").appName("commcoach-communication-trends").getOrCreate()
        frame = spark.createDataFrame(filtered)
        trend_frame = (
            frame.withColumn("created_label", F.date_format(F.to_timestamp("created_at"), "MMM dd"))
            .groupBy("created_label")
            .agg(
                F.round(F.avg("confidence_score"), 0).alias("confidence_score"),
                F.round(F.avg("communication_score"), 0).alias("communication_score"),
                F.round(F.avg(F.col("analytics.words_per_minute")), 2).alias("average_wpm"),
                F.round(F.avg(F.col("analytics.filler_word_total")), 2).alias("average_filler"),
            )
            .orderBy("created_label")
        )
        trend_points = [
            {
                "label": row["created_label"],
                "confidence_score": int(row["confidence_score"] or 0),
                "communication_score": int(row["communication_score"] or 0),
            }
            for row in trend_frame.collect()[-6:]
        ]
        averages_row = frame.agg(
            F.round(F.avg(F.col("analytics.words_per_minute")), 2).alias("average_words_per_minute"),
            F.round(F.avg(F.col("analytics.filler_word_total")), 2).alias("average_filler_words"),
            F.round(F.avg("communication_score"), 2).alias("average_communication_score"),
        ).collect()[0]
        spark.stop()
        return {
            "average_words_per_minute": float(averages_row["average_words_per_minute"] or 0.0),
            "average_filler_words": float(averages_row["average_filler_words"] or 0.0),
            "average_communication_score": float(averages_row["average_communication_score"] or 0.0),
            "trend_points": trend_points,
        }
    except Exception:
        ordered = sorted(
            filtered,
            key=lambda row: datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00")),
        )
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in ordered:
            created_at = datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00"))
            grouped.setdefault(created_at.strftime("%b %d"), []).append(row)

        trend_points = []
        for label, label_rows in list(grouped.items())[-6:]:
            trend_points.append(
                {
                    "label": label,
                    "confidence_score": round(
                        sum(float(item.get("confidence_score", 0) or 0) for item in label_rows) / len(label_rows)
                    ),
                    "communication_score": round(
                        sum(float(item.get("communication_score", 0) or 0) for item in label_rows)
                        / len(label_rows)
                    ),
                }
            )

        wpm_values = [
            float((row.get("analytics") or {}).get("words_per_minute", 0) or 0)
            for row in filtered
        ]
        filler_values = [
            float((row.get("analytics") or {}).get("filler_word_total", 0) or 0)
            for row in filtered
        ]
        return {
            "average_words_per_minute": round(sum(wpm_values) / len(wpm_values), 2) if wpm_values else 0.0,
            "average_filler_words": round(sum(filler_values) / len(filler_values), 2) if filler_values else 0.0,
            "average_communication_score": round(
                sum(float(row.get("communication_score", 0) or 0) for row in filtered) / len(filtered),
                2,
            ),
            "trend_points": trend_points,
        }


def main(source_path: str = "reports/final") -> None:
    print(json.dumps(build_communication_trends(_load_rows(source_path)), indent=2))


if __name__ == "__main__":
    main()
