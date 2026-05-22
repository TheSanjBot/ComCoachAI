from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_modes() -> list[dict[str, str]]:
    return [
        {
            "id": "interview",
            "title": "Interview Training Mode",
            "description": "Practice structured technical interviews with contextual follow-up questions.",
        },
        {
            "id": "public_speaking",
            "title": "Public Speaking Training Mode",
            "description": "Improve pacing, confidence, posture, and storytelling flow after each speech.",
        },
        {
            "id": "resume_analysis",
            "title": "Resume + Skill Gap Analysis Mode",
            "description": "Compare resume strengths against target roles and generate a learning roadmap.",
        },
    ]

