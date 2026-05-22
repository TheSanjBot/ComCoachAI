from backend.app.services.communication_analysis_service import communication_analysis_service


def test_communication_analysis_detects_fillers_and_pace():
    result = communication_analysis_service.analyze(
        "Um I actually like this approach because it keeps the API stable and easier to evolve.",
        [
            {"start": 0.0, "end": 2.0, "text": "Um I actually like this approach"},
            {"start": 2.3, "end": 6.0, "text": "because it keeps the API stable and easier to evolve"},
        ],
    )

    assert result["filler_count"] >= 3
    assert result["wpm"] > 0
    assert result["pace"] in {"slow", "ideal", "fast"}

