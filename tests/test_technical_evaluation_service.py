from backend.app.services.technical_evaluation_service import technical_evaluation_service


def test_technical_evaluation_scores_expected_concepts():
    result = technical_evaluation_service.evaluate(
        question_context={
            "expected_concepts": ["versioning", "pagination", "authentication"]
        },
        answer="I would start with versioning the API and add authentication for protected endpoints.",
        role="Backend Engineer",
    )

    assert result["technical_score"] > 0
    assert "versioning" in result["matched_concepts"]
