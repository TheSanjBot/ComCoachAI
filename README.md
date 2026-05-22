# CommCoach AI

CommCoach AI is a prototype-scale interview and communication coaching platform built around a staged workflow: lightweight live capture first, deeper AI analysis after submit, and modular services for coaching, memory, recommendations, analytics, and reporting.

## Implemented Scope

This repository now covers **Stages 1 through 15**:

- Next.js + TypeScript + Tailwind + shadcn-style frontend
- FastAPI + async SQLAlchemy backend with JWT auth
- Homepage-integrated dashboard
- Interview Training Mode
- Public Speaking Training Mode
- Resume + Skill Gap Analysis Mode
- Hybrid webcam/mic capture with staged post-submit processing
- Audio extraction, WhisperX transcription, and communication analysis
- OpenCV + MediaPipe eye-contact, posture, and lightweight malpractice analysis
- LangChain-backed interview evaluation and follow-up generation with graceful fallback
- Semantic memory with local ChromaDB storage and file fallback
- Personalized coaching and upskilling recommendations
- Lightweight PySpark analytics scripts
- Persisted final reports in PostgreSQL plus JSON artifacts under `reports/`
- Docker / docker-compose deployment scaffolding

## Repository Structure

```text
project/
├── frontend/
├── backend/
├── pyspark/
├── uploads/
├── reports/
├── tests/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Local Setup

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy backend\.env.example backend\.env
copy backend\.env.secrets.example backend\.env.secrets
cd backend
uvicorn app.main:app --reload
```

Keep non-secret runtime values in `backend/.env` and API keys in `backend/.env.secrets`.

Useful secrets/placeholders:

- `NVIDIA_NIM_API_KEY`
- `TAVILY_API_KEY`
- `LANGSMITH_API_KEY`

### Frontend

```bash
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

### Docker Compose

```bash
docker compose up --build
```

This starts:

- `frontend` on `http://localhost:3000`
- `backend` on `http://localhost:8000`
- `postgres` on `localhost:5432`
## API Endpoints

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/dashboard/overview`
- `POST /api/v1/recordings/upload`
- `POST /api/v1/recordings/{recording_id}/analyze`
- `GET /api/v1/recordings/{recording_id}/analysis`
- `POST /api/v1/interview/sessions`
- `GET /api/v1/interview/sessions/{session_id}`
- `POST /api/v1/interview/sessions/{session_id}/submit`
- `GET /api/v1/interview/sessions/{session_id}/report`
- `POST /api/v1/public-speaking/sessions`
- `GET /api/v1/public-speaking/sessions/{session_id}`
- `POST /api/v1/public-speaking/sessions/{session_id}/coach`
- `POST /api/v1/resume-analysis/text`
- `POST /api/v1/resume-analysis/upload`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{report_id}`
- `GET /api/v1/health`

## Stage 13 Analytics

Run lightweight batch analytics against persisted report artifacts:

```bash
python pyspark/communication_trends.py
python pyspark/interview_analytics.py
```

The scripts prefer PySpark when available and fall back to local Python aggregation otherwise.

## Deployment Targets

- Frontend: Vercel
- Backend: Render
- PostgreSQL: Neon
- Vector memory: local ChromaDB

## Testing

```bash
set PYTHONPATH=backend
pytest tests/backend
```
