from backend.app.services.resume_analysis_service import resume_analysis_service


def test_resume_analysis_finds_missing_skills():
    result = resume_analysis_service.analyze_text(
        resume_text="Backend engineer with Python, FastAPI, SQL and REST API experience.",
        target_role="Backend Engineer",
    )

    assert "python" in result["detected_skills"]
    assert isinstance(result["missing_skills"], list)
    assert result["matching_score"] >= 0

