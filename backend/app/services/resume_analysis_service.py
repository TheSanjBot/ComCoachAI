from __future__ import annotations

from dataclasses import dataclass, field
import re

import fitz
from fastapi import HTTPException, UploadFile, status
import spacy
from spacy.matcher import PhraseMatcher

from app.models.user import User
from app.schemas.report import LearningRoadmapItem
from app.schemas.resume import ResumeAnalysisResponse
from app.services.coaching_service import coaching_service
from app.services.memory_service import memory_service
from app.services.recommendation_service import recommendation_service

ROLE_SKILLS = {
    "SDE": {"python", "algorithms", "data structures", "sql", "testing"},
    "Frontend Engineer": {"react", "typescript", "javascript", "css", "testing"},
    "Backend Engineer": {"python", "fastapi", "sql", "docker", "api design"},
    "Cloud Engineer": {"aws", "docker", "kubernetes", "terraform", "networking"},
    "DevOps Engineer": {"ci/cd", "docker", "kubernetes", "terraform", "linux"},
    "SRE": {"observability", "incident response", "kubernetes", "linux", "slo"},
    "Testing Engineer": {"automation", "selenium", "api testing", "pytest", "ci/cd"},
    "AI/ML Engineer": {"python", "pytorch", "machine learning", "llm", "sql"},
    "Data Analyst": {"sql", "python", "excel", "tableau", "statistics"},
}

SKILL_ALIASES = {
    "python": ["python", "flask", "django", "fastapi scripting"],
    "react": ["react", "react.js", "reactjs", "next.js", "nextjs"],
    "typescript": ["typescript", "type script"],
    "javascript": ["javascript", "ecmascript", "node.js", "nodejs"],
    "css": ["css", "scss", "sass", "tailwind", "styled-components"],
    "fastapi": ["fastapi", "async api", "python api"],
    "docker": ["docker", "containerization", "containers"],
    "kubernetes": ["kubernetes", "k8s"],
    "terraform": ["terraform", "infrastructure as code", "iac"],
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda", "cloudformation"],
    "linux": ["linux", "ubuntu", "bash", "shell scripting"],
    "sql": ["sql", "postgresql", "mysql", "sqlite", "sqlalchemy"],
    "pytest": ["pytest", "py test"],
    "selenium": ["selenium", "webdriver"],
    "pytorch": ["pytorch", "torch"],
    "tableau": ["tableau", "data visualization dashboards"],
    "statistics": ["statistics", "hypothesis testing", "probability", "a/b testing"],
    "observability": ["observability", "monitoring", "prometheus", "grafana", "tracing"],
    "incident response": ["incident response", "on-call", "postmortem", "root cause analysis", "pagerduty"],
    "machine learning": ["machine learning", "ml", "classification", "regression", "model training"],
    "llm": ["llm", "large language model", "rag", "transformers", "prompt engineering"],
    "api testing": ["api testing", "postman", "contract testing", "integration api tests"],
    "ci/cd": ["ci/cd", "continuous integration", "continuous delivery", "github actions", "jenkins", "gitlab ci"],
    "api design": ["api design", "rest api", "rest apis", "restful api", "restful apis", "graphql", "microservices"],
    "algorithms": ["algorithms", "algorithmic problem solving", "time complexity"],
    "data structures": ["data structures", "hashmap", "hash map", "linked list", "tree", "graph"],
    "automation": ["automation", "test automation", "workflow automation"],
    "excel": ["excel", "pivot table", "vlookup", "spreadsheets"],
    "networking": ["networking", "tcp/ip", "dns", "load balancer", "routing"],
    "slo": ["slo", "service level objective", "sli", "sla"],
    "testing": ["testing", "unit testing", "integration testing", "quality assurance"],
}

SECTION_WEIGHTS = {
    "skills": 2.6,
    "experience": 2.2,
    "projects": 2.2,
    "summary": 1.8,
    "certifications": 1.8,
    "education": 1.1,
    "other": 1.0,
}

SECTION_PATTERNS = {
    "skills": ("skills", "technical skills", "tech stack", "competencies"),
    "experience": ("experience", "work experience", "professional experience", "employment"),
    "projects": ("projects", "project experience", "selected projects"),
    "summary": ("summary", "profile", "professional summary", "about"),
    "certifications": ("certifications", "certificates"),
    "education": ("education", "academics"),
}

ACTION_VERBS = {
    "built",
    "designed",
    "developed",
    "deployed",
    "implemented",
    "created",
    "optimized",
    "improved",
    "migrated",
    "maintained",
    "scaled",
    "automated",
    "owned",
    "led",
    "analyzed",
}


@dataclass
class SkillEvidence:
    skill: str
    score: float = 0.0
    aliases: set[str] = field(default_factory=set)
    sections: set[str] = field(default_factory=set)
    contexts: list[str] = field(default_factory=list)

    def register(self, *, alias: str, section: str, context: str, score: float) -> None:
        self.aliases.add(alias)
        self.sections.add(section)
        if context and context not in self.contexts:
            self.contexts.append(context)
        self.score += score


class ResumeAnalysisService:
    def __init__(self) -> None:
        self._nlp = spacy.blank("en")
        if "sentencizer" not in self._nlp.pipe_names:
            self._nlp.add_pipe("sentencizer")
        self._matcher = PhraseMatcher(self._nlp.vocab, attr="LOWER")
        for skill, aliases in SKILL_ALIASES.items():
            phrases = [self._nlp.make_doc(text) for text in {skill, *aliases}]
            self._matcher.add(skill, phrases)

    async def extract_text_from_upload(self, resume: UploadFile) -> str:
        filename = (resume.filename or "").lower()
        content = await resume.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded resume file was empty.")

        if filename.endswith(".pdf"):
            document = fitz.open(stream=content, filetype="pdf")
            return "\n".join(page.get_text("text") for page in document).strip()

        if filename.endswith(".txt") or filename.endswith(".md"):
            return content.decode("utf-8", errors="ignore").strip()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported resume format. Please upload a PDF or TXT file.",
        )

    async def analyze_text(
        self,
        *,
        user: User,
        resume_text: str,
        target_role: str,
    ) -> ResumeAnalysisResponse:
        required_skills = ROLE_SKILLS.get(target_role, set())
        evidence_by_skill = self._extract_skill_evidence(resume_text)
        detected_skills = sorted(
            skill
            for skill, evidence in evidence_by_skill.items()
            if self._is_confirmed_skill(skill, evidence, required_skills)
        )
        missing_skills = sorted(skill for skill in required_skills if skill not in detected_skills)
        matching_score = round((len(required_skills) - len(missing_skills)) / max(len(required_skills), 1) * 100, 2)
        ats_readiness_score = self._ats_readiness_score(resume_text, sections_count=self._section_count(resume_text))

        roadmap_resources = await recommendation_service.recommend(missing_skills, include_communication=False)
        roadmap_lookup = {resource.topic.lower(): resource for resource in roadmap_resources}
        learning_roadmap = [
            LearningRoadmapItem(
                skill=skill,
                next_step=self._learning_step(skill, target_role),
                resource_title=roadmap_lookup.get(skill.lower()).title if roadmap_lookup.get(skill.lower()) else None,
                resource_url=roadmap_lookup.get(skill.lower()).url if roadmap_lookup.get(skill.lower()) else None,
            )
            for skill in missing_skills[:5]
        ]

        strongest_detected = self._top_detected_strengths(detected_skills, evidence_by_skill)
        priority_gaps = self._priority_gap_messages(missing_skills, target_role)
        memory_context = memory_service.retrieve_user_context(str(user.id), target_role, limit=3)
        personalized_coaching = coaching_service.personalize(
            mode="resume-skill-gap",
            strengths=strongest_detected,
            weaknesses=[f"Missing {skill} for {target_role} alignment." for skill in missing_skills[:3]],
            current_focus_topics=missing_skills[:3],
            memory_context=memory_context,
        )

        extracted_text_preview = re.sub(r"\s+", " ", resume_text).strip()[:300]
        return ResumeAnalysisResponse(
            target_role=target_role,
            matching_score=matching_score,
            ats_readiness_score=ats_readiness_score,
            role_fit_summary=self._role_fit_summary(target_role, matching_score, missing_skills, strongest_detected),
            detected_skills=detected_skills,
            missing_skills=missing_skills,
            priority_gaps=priority_gaps,
            evidence_highlights=strongest_detected,
            extracted_text_preview=extracted_text_preview,
            learning_roadmap=learning_roadmap,
            recommendations=roadmap_resources,
            personalized_coaching=personalized_coaching,
        )

    def _extract_skill_evidence(self, resume_text: str) -> dict[str, SkillEvidence]:
        normalized_text = self._normalize_resume_text(resume_text)
        sections = self._split_sections(normalized_text)
        evidence_by_skill: dict[str, SkillEvidence] = {}

        for section_name, section_text in sections:
            if not section_text.strip():
                continue
            doc = self._nlp(section_text)
            matches = self._matcher(doc)
            sentence_ranges = list(doc.sents)
            for match_id, start, end in matches:
                skill = self._nlp.vocab.strings[match_id]
                span = doc[start:end]
                sentence = self._sentence_for_span(sentence_ranges, span.start, span.end)
                context = self._clean_context(sentence.text if sentence is not None else span.sent.text if span.sent else span.text)
                score = self._score_match(section_name, context, span.text)
                evidence_by_skill.setdefault(skill, SkillEvidence(skill=skill)).register(
                    alias=span.text.lower(),
                    section=section_name,
                    context=context,
                    score=score,
                )

        return evidence_by_skill

    @staticmethod
    def _normalize_resume_text(resume_text: str) -> str:
        cleaned = resume_text.replace("\r", "\n")
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned

    def _split_sections(self, resume_text: str) -> list[tuple[str, str]]:
        lines = [line.strip() for line in resume_text.splitlines()]
        sections: list[tuple[str, list[str]]] = [("other", [])]
        current_section = "other"

        for line in lines:
            if not line:
                continue
            normalized = re.sub(r"[^a-zA-Z ]", "", line).strip().lower()
            mapped_section = self._section_name(normalized)
            if mapped_section is not None and len(normalized.split()) <= 4:
                current_section = mapped_section
                sections.append((current_section, []))
                continue
            sections[-1][1].append(line)

        return [
            (name, "\n".join(content))
            for name, content in sections
            if content
        ]

    @staticmethod
    def _section_name(normalized_heading: str) -> str | None:
        for section_name, patterns in SECTION_PATTERNS.items():
            if normalized_heading in patterns:
                return section_name
        return None

    @staticmethod
    def _sentence_for_span(sentences, start: int, end: int):
        for sentence in sentences:
            if sentence.start <= start and sentence.end >= end:
                return sentence
        return None

    @staticmethod
    def _clean_context(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()[:180]

    def _score_match(self, section_name: str, context: str, alias: str) -> float:
        score = SECTION_WEIGHTS.get(section_name, 1.0)
        context_lower = context.lower()
        alias_lower = alias.lower()

        if any(verb in context_lower for verb in ACTION_VERBS):
            score += 1.0
        if re.search(r"\b\d+\+?\s+(years?|yrs?)\b", context_lower):
            score += 0.6
        if any(marker in context_lower for marker in ("certified", "certification", "production", "deployed", "implemented")):
            score += 0.5
        if alias_lower in context_lower and "," in context_lower and len(context_lower.split()) < 24:
            score += 0.4

        return score

    @staticmethod
    def _is_confirmed_skill(
        skill: str,
        evidence: SkillEvidence,
        required_skills: set[str],
    ) -> bool:
        threshold = 1.7 if skill in required_skills else 2.1
        return evidence.score >= threshold

    @staticmethod
    def _learning_step(skill: str, target_role: str) -> str:
        return f"Build one role-relevant proof point for {skill} so your {target_role} resume shows hands-on evidence, not just a mention."

    def _ats_readiness_score(self, resume_text: str, *, sections_count: int) -> float:
        normalized = resume_text.lower()
        action_verb_hits = sum(1 for verb in ACTION_VERBS if verb in normalized)
        quantified_hits = len(re.findall(r"\b\d+(?:\.\d+)?%|\b\d+\+?\s*(?:users|projects|apis|services|models|pipelines|years?)", normalized))
        section_score = min(sections_count * 12, 36)
        action_score = min(action_verb_hits * 4, 28)
        quantified_score = min(quantified_hits * 6, 24)
        length_score = 12 if 350 <= len(normalized.split()) <= 900 else 6
        return round(min(section_score + action_score + quantified_score + length_score, 100), 2)

    def _section_count(self, resume_text: str) -> int:
        return len([1 for name, _ in self._split_sections(self._normalize_resume_text(resume_text)) if name])

    @staticmethod
    def _priority_gap_messages(missing_skills: list[str], target_role: str) -> list[str]:
        return [
            f"{skill} is a high-priority gap for {target_role} and should show up with project evidence, not just coursework."
            for skill in missing_skills[:4]
        ]

    @staticmethod
    def _role_fit_summary(
        target_role: str,
        matching_score: float,
        missing_skills: list[str],
        strongest_detected: list[str],
    ) -> str:
        if matching_score >= 75:
            return f"Your resume is already broadly aligned to {target_role}, with the strongest evidence concentrated in recent technical work."
        if matching_score >= 50:
            top_gap = missing_skills[0] if missing_skills else "a few role-specific proof points"
            return f"Your resume shows a workable base for {target_role}, but it still needs clearer evidence around {top_gap}."
        anchor = strongest_detected[0] if strongest_detected else "foundational experience"
        return f"Your resume needs stronger role-specific positioning for {target_role}. Start by turning {anchor} into sharper, outcome-driven project bullets."

    @staticmethod
    def _top_detected_strengths(
        detected_skills: list[str],
        evidence_by_skill: dict[str, SkillEvidence],
    ) -> list[str]:
        ranked = sorted(
            (evidence_by_skill[skill] for skill in detected_skills if skill in evidence_by_skill),
            key=lambda item: item.score,
            reverse=True,
        )
        strengths: list[str] = []
        for item in ranked[:3]:
            contexts = item.contexts[:1]
            if contexts:
                strengths.append(f"{item.skill} appears with concrete resume evidence: {contexts[0]}")
            else:
                strengths.append(f"{item.skill} is supported by multiple contextual matches in the resume.")
        return strengths

resume_analysis_service = ResumeAnalysisService()
