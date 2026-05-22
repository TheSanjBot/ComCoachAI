from __future__ import annotations

import httpx
from urllib.parse import urlparse

from app.core.config import settings
from app.schemas.report import ResourceRecommendation

APPROVED_COURSE_DOMAINS = [
    "coursera.org",
    "udemy.com",
    "edx.org",
    "pluralsight.com",
    "frontendmasters.com",
    "codecademy.com",
    "skillshare.com",
    "skillsoft.com",
]

COURSE_PATH_TOKENS = [
    "/learn",
    "/course",
    "/courses",
    "/specialization",
    "/specializations",
    "/professional-certificate",
    "/professional-certificates",
    "/class",
    "/paths",
    "/skill-path",
]

REJECTED_PATH_TOKENS = [
    "/search",
    "/blog",
    "/articles",
    "/article",
    "/docs",
    "/help",
    "/support",
    "/pricing",
    "/login",
    "/signup",
]

REJECTED_TITLE_TERMS = [
    "reddit",
    "quora",
    "wikipedia",
    "blog",
    "forum",
    "community",
]


class RecommendationService:
    async def recommend(
        self,
        weak_topics: list[str],
        *,
        include_communication: bool = True,
        max_results: int = 6,
    ) -> list[ResourceRecommendation]:
        if not settings.tavily_api_key:
            raise RuntimeError("Tavily API key is not configured.")

        topics = [topic for topic in weak_topics if topic]
        if include_communication and "communication" not in {topic.lower() for topic in topics}:
            topics.append("communication")
        return await self._recommend_with_tavily(topics, max_results)

    async def _recommend_with_tavily(
        self,
        topics: list[str],
        max_results: int,
    ) -> list[ResourceRecommendation]:
        recommendations: list[ResourceRecommendation] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(timeout=20.0) as client:
            for topic in topics:
                query = (
                    f"{topic} online course OR specialization OR professional certificate "
                    f"site:coursera.org OR site:udemy.com OR site:edx.org OR site:pluralsight.com "
                    f"OR site:frontendmasters.com OR site:codecademy.com OR site:skillshare.com OR site:skillsoft.com"
                )
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": settings.tavily_api_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": 5,
                        "include_domains": APPROVED_COURSE_DOMAINS,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                for result in payload.get("results", []):
                    url = str(result.get("url", "")).strip()
                    title = str(result.get("title", "Learning Resource")).strip()
                    if (
                        not url
                        or url in seen_urls
                        or not self._is_allowed_course_url(url)
                        or not self._looks_course_like_result(title, url)
                    ):
                        continue
                    platform = self._platform_from_url(url)
                    if platform == "Course":
                        continue
                    recommendations.append(
                        ResourceRecommendation(
                            topic=topic,
                            title=title,
                            platform=platform,
                            price="Unknown",
                            url=url,
                        )
                    )
                    seen_urls.add(url)
                    if len(recommendations) >= max_results:
                        return recommendations

        return recommendations

    @staticmethod
    def _platform_from_url(url: str) -> str:
        lowered = url.lower()
        if "udemy" in lowered:
            return "Udemy"
        if "coursera" in lowered:
            return "Coursera"
        if "edx" in lowered:
            return "edX"
        if "pluralsight" in lowered:
            return "Pluralsight"
        if "frontendmasters" in lowered:
            return "Frontend Masters"
        if "codecademy" in lowered:
            return "Codecademy"
        if "skillshare" in lowered:
            return "Skillshare"
        if "skillsoft" in lowered:
            return "Skillsoft"
        return "Course"

    @staticmethod
    def _is_allowed_course_url(url: str) -> bool:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        if not any(domain.endswith(allowed) for allowed in APPROVED_COURSE_DOMAINS):
            return False
        path = parsed.path.lower()
        if any(token in path for token in REJECTED_PATH_TOKENS):
            return False
        return any(token in path for token in COURSE_PATH_TOKENS)

    @staticmethod
    def _looks_course_like_result(title: str, url: str) -> bool:
        lowered_title = title.lower()
        lowered_url = url.lower()
        if any(term in lowered_title for term in REJECTED_TITLE_TERMS):
            return False
        return any(token.strip("/") in lowered_title or token in lowered_url for token in COURSE_PATH_TOKENS)


recommendation_service = RecommendationService()
