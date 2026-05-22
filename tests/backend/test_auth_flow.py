import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./tests/test_commcoach.db")
os.environ.setdefault("SECRET_KEY", "stage1-test-secret")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("UPLOADS_DIR", "tests/uploads")

from app.main import app  # noqa: E402
from app.schemas.coaching import TechnicalEvaluationResult  # noqa: E402
from app.schemas.report import ResourceRecommendation  # noqa: E402


def test_signup_login_and_fetch_profile():
    unique_email = f"stage1-{uuid4().hex[:8]}@example.com"
    sample_recording = (ROOT_DIR / "tests" / "sample-stage4-6.mp4").read_bytes()
    mocked_recommendations = [
        ResourceRecommendation(
            topic="docker",
            title="Docker Docs",
            platform="Official Docs",
            price="Free",
            url="https://docs.docker.com/",
        ),
        ResourceRecommendation(
            topic="communication",
            title="Public Speaking",
            platform="Coursera",
            price="Free / Paid Certificate",
            url="https://www.coursera.org/learn/public-speaking",
        ),
    ]

    with patch(
        "app.services.interview_llm_service.InterviewLLMService.evaluate_answer",
        return_value=TechnicalEvaluationResult(
            technical_score=82,
            correctness_score=84,
            explanation_depth_score=78,
            technical_clarity_score=83,
            strengths=["Explained the concept clearly."],
            weaknesses=["Missed one networking edge case."],
            missing_concepts=["service discovery"],
            evidence_found=["docker bridge networking"],
            suggested_followup_topics=["kubernetes networking"],
            summary="Strong answer with one missing concept.",
            strategy="test-mock",
            warnings=[],
        ),
    ), patch(
        "app.services.recommendation_service.RecommendationService.recommend",
        new=AsyncMock(return_value=mocked_recommendations),
    ), TestClient(app) as client:
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": unique_email,
                "full_name": "Stage One Tester",
                "password": "securepass123"
            },
        )

        assert signup_response.status_code == 201
        signup_payload = signup_response.json()
        assert "access_token" in signup_payload
        assert signup_payload["user"]["email"] == unique_email

        token = signup_payload["access_token"]

        profile_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == unique_email

        overview_response = client.get(
            "/api/v1/dashboard/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert overview_response.status_code == 200
        overview_payload = overview_response.json()
        assert overview_payload["welcome_name"] == "Stage"
        assert len(overview_payload["mode_cards"]) == 3
        assert overview_payload["recommended_mode_slug"] == "interview-training"

        upload_response = client.post(
            "/api/v1/recordings/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"recording": ("sample.mp4", sample_recording, "video/mp4")},
            data={
                "mode": "interview-training",
                "duration_seconds": "12",
                "face_detection_state": "detected",
                "face_detected_samples": "5",
                "face_missing_samples": "1",
            },
        )
        assert upload_response.status_code == 201
        upload_payload = upload_response.json()
        assert upload_payload["mode"] == "interview-training"
        assert upload_payload["processing_status"] == "stored"
        assert upload_payload["duration_seconds"] == 12

        analysis_response = client.post(
            f"/api/v1/recordings/{upload_payload['recording_id']}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert analysis_response.status_code == 200
        analysis_payload = analysis_response.json()
        assert analysis_payload["recording_id"] == upload_payload["recording_id"]
        assert analysis_payload["processing_status"] in {"analyzed", "partial"}
        assert "audio_processing" in analysis_payload
        assert "communication_analysis" in analysis_payload
        assert "video_analysis" in analysis_payload

        interview_session_response = client.post(
            "/api/v1/interview/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "role": "Backend Engineer",
                "experience_level": "mid-level",
                "target_question_count": 1,
                "resume_notes": "Strong API fundamentals, weaker Docker depth."
            },
        )
        assert interview_session_response.status_code == 201
        interview_session_payload = interview_session_response.json()
        assert interview_session_payload["role"] == "Backend Engineer"
        assert interview_session_payload["current_question"] is not None

        interview_submit_response = client.post(
            f"/api/v1/interview/sessions/{interview_session_payload['session_id']}/submit",
            headers={"Authorization": f"Bearer {token}"},
            json={"recording_id": upload_payload["recording_id"]},
        )
        assert interview_submit_response.status_code == 200
        interview_submit_payload = interview_submit_response.json()
        assert interview_submit_payload["technical_evaluation"]["technical_score"] >= 0
        assert interview_submit_payload["session"]["status"] in {"active", "completed"}
        assert interview_submit_payload["final_report"] is not None

        public_speaking_session_response = client.post(
            "/api/v1/public-speaking/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"topic": "Explain observability basics", "audience": "Hiring panel"},
        )
        assert public_speaking_session_response.status_code == 201
        public_speaking_session_payload = public_speaking_session_response.json()
        assert public_speaking_session_payload["topic"] == "Explain observability basics"

        public_speaking_coach_response = client.post(
            f"/api/v1/public-speaking/sessions/{public_speaking_session_payload['session_id']}/coach",
            headers={"Authorization": f"Bearer {token}"},
            json={"recording_id": upload_payload["recording_id"]},
        )
        assert public_speaking_coach_response.status_code == 200
        public_speaking_coach_payload = public_speaking_coach_response.json()
        assert public_speaking_coach_payload["confidence_score"] >= 0
        assert public_speaking_coach_payload["summary"]
        assert public_speaking_coach_payload["report_id"]

        resume_analysis_response = client.post(
            "/api/v1/resume-analysis/text",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "resume_text": (
                    "Technical Skills\n"
                    "Python, FastAPI, PostgreSQL, Docker, REST APIs\n\n"
                    "Experience\n"
                    "Built backend services with Python and FastAPI, designed RESTful APIs, "
                    "and deployed containerized applications with Docker.\n"
                ),
                "target_role": "Backend Engineer",
            },
        )
        assert resume_analysis_response.status_code == 200
        resume_analysis_payload = resume_analysis_response.json()
        assert resume_analysis_payload["target_role"] == "Backend Engineer"
        assert resume_analysis_payload["report_id"]
        assert "fastapi" in resume_analysis_payload["detected_skills"]
        assert "api design" in resume_analysis_payload["detected_skills"]

        resume_upload_response = client.post(
            "/api/v1/resume-analysis/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "resume": (
                    "resume.txt",
                    (
                        b"Professional Experience\n"
                        b"Implemented CI/CD workflows with GitHub Actions and deployed services to AWS.\n"
                        b"Worked with k8s and Terraform for infrastructure automation.\n"
                    ),
                    "text/plain",
                )
            },
            data={"target_role": "DevOps Engineer"},
        )
        assert resume_upload_response.status_code == 200
        resume_upload_payload = resume_upload_response.json()
        assert resume_upload_payload["report_id"]
        assert "ci/cd" in resume_upload_payload["detected_skills"]
        assert "kubernetes" in resume_upload_payload["detected_skills"]
        assert "terraform" in resume_upload_payload["detected_skills"]

        reports_response = client.get(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert reports_response.status_code == 200
        reports_payload = reports_response.json()
        assert len(reports_payload["reports"]) >= 3

        first_report_id = reports_payload["reports"][0]["report_id"]
        report_detail_response = client.get(
            f"/api/v1/reports/{first_report_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert report_detail_response.status_code == 200
        assert report_detail_response.json()["report_id"] == first_report_id

        updated_overview_response = client.get(
            "/api/v1/dashboard/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert updated_overview_response.status_code == 200
        updated_overview_payload = updated_overview_response.json()
        assert updated_overview_payload["total_sessions"] >= 3
        assert updated_overview_payload["recent_reports"]

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "securepass123"},
        )
        assert login_response.status_code == 200
        assert login_response.json()["user"]["email"] == unique_email
