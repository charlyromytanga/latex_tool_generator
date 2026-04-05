"""LLM extraction and matching orchestration (Level 2).

Current implementation is heuristic and DB-backed, ready to be replaced by real LLM calls.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

from .config import OrchestrationConfig
from .database import Database


LOGGER = logging.getLogger(__name__)


TECH_KEYWORDS = {
    "python",
    "sql",
    "fastapi",
    "streamlit",
    "docker",
    "kubernetes",
    "git",
    "linux",
    "pandas",
    "numpy",
    "latex",
}

SOFT_KEYWORDS = {
    "communication",
    "leadership",
    "teamwork",
    "autonomy",
    "problem solving",
}

DOMAIN_KEYWORDS = {
    "finance",
    "fintech",
    "quant",
    "data",
    "ai",
    "machine learning",
}


@dataclass(frozen=True)
class OfferKeywords:
    offer_id: str
    technical: list[str]
    soft_skills: list[str]
    domains: list[str]
    seniority: str


class MatchingRepositoryGateway:
    """Gateway for loading profile entities and persisting extraction/matching results."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def fetch_offer(self, offer_id: str) -> dict[str, Any]:
        row = self.database.fetch_one(
            "SELECT offer_id, raw_text, sections_json FROM offers_raw WHERE offer_id = :offer_id",
            {"offer_id": offer_id},
        )
        if row is None:
            raise ValueError(f"Offer not found: {offer_id}")
        return row

    def upsert_offer_keywords(self, offer_keywords: OfferKeywords, model_version: str) -> None:
        payload = {
            "keyword_id": str(uuid4()),
            "offer_id": offer_keywords.offer_id,
            "keywords_json": json.dumps(
                {
                    "technical": offer_keywords.technical,
                    "soft_skills": offer_keywords.soft_skills,
                    "domain": offer_keywords.domains,
                    "seniority": offer_keywords.seniority,
                },
                ensure_ascii=True,
            ),
            "model_version": model_version,
        }

        sql = """
        INSERT INTO offer_keywords (keyword_id, offer_id, keywords_json, model_version)
        VALUES (:keyword_id, :offer_id, :keywords_json, :model_version)
        """

        self.database.execute(sql, payload)

    def fetch_experiences(self) -> list[dict[str, Any]]:
        return self.database.fetch_all(
            "SELECT exp_id, company, role, description, skills_json FROM my_experiences"
        )

    def fetch_projects(self) -> list[dict[str, Any]]:
        return self.database.fetch_all(
            "SELECT project_id, repo_name, description, languages_json, technologies_json FROM my_projects"
        )

    def fetch_formations(self) -> list[dict[str, Any]]:
        return self.database.fetch_all(
            "SELECT formation_id, institution, program, courses_json, course_categories_json FROM formations"
        )

    def insert_matching_score(
        self,
        *,
        offer_id: str,
        match_type: str,
        exp_id: str | None,
        project_id: str | None,
        score: float,
        reasoning: str,
        model_version: str,
    ) -> None:
        sql = """
        INSERT INTO matching_scores (
            match_id,
            offer_id,
            match_type,
            exp_id,
            project_id,
            match_score,
            reasoning,
            model_version,
            computed_at
        ) VALUES (
            :match_id,
            :offer_id,
            :match_type,
            :exp_id,
            :project_id,
            :match_score,
            :reasoning,
            :model_version,
            :computed_at
        )
        """
        self.database.execute(
            sql,
            {
                "match_id": str(uuid4()),
                "offer_id": offer_id,
                "match_type": match_type,
                "exp_id": exp_id,
                "project_id": project_id,
                "match_score": score,
                "reasoning": reasoning,
                "model_version": model_version,
                "computed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            },
        )

    def insert_formation_matching_score(
        self,
        *,
        offer_id: str,
        formation_id: str,
        score: float,
        reasoning: str,
        model_version: str,
    ) -> None:
        sql = """
        INSERT INTO formation_matching_scores (
            match_id,
            offer_id,
            formation_id,
            match_score,
            reasoning,
            model_version,
            computed_at
        ) VALUES (
            :match_id,
            :offer_id,
            :formation_id,
            :match_score,
            :reasoning,
            :model_version,
            :computed_at
        )
        """
        self.database.execute(
            sql,
            {
                "match_id": str(uuid4()),
                "offer_id": offer_id,
                "formation_id": formation_id,
                "match_score": score,
                "reasoning": reasoning,
                "model_version": model_version,
                "computed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            },
        )


class HeuristicKeywordExtractor:
    """Keyword extractor compatible with future LLM interface."""

    def extract(self, offer_id: str, raw_text: str) -> OfferKeywords:
        content = raw_text.lower()
        technical = sorted([keyword for keyword in TECH_KEYWORDS if keyword in content])
        soft_skills = sorted([keyword for keyword in SOFT_KEYWORDS if keyword in content])
        domains = sorted([keyword for keyword in DOMAIN_KEYWORDS if keyword in content])

        seniority = "mid"
        if "junior" in content:
            seniority = "junior"
        elif "senior" in content or "lead" in content:
            seniority = "senior"

        return OfferKeywords(
            offer_id=offer_id,
            technical=technical,
            soft_skills=soft_skills,
            domains=domains,
            seniority=seniority,
        )


class OfferLLMOrchestrator:
    """Coordinates extraction and matching for one offer id."""

    def __init__(self, config: OrchestrationConfig) -> None:
        self.config = config
        self.repo = MatchingRepositoryGateway(Database(config.database_url))
        self.extractor = HeuristicKeywordExtractor()

    def run(self, offer_id: str) -> dict[str, Any]:
        offer = self.repo.fetch_offer(offer_id)
        raw_text = str(offer["raw_text"])

        keywords = self.extractor.extract(offer_id=offer_id, raw_text=raw_text)
        self.repo.upsert_offer_keywords(keywords, self.config.model_version)

        inserted_matches = self._match_experiences_and_projects(offer_id, keywords)
        inserted_formations = self._match_formations(offer_id, keywords)

        return {
            "offer_id": offer_id,
            "keywords": {
                "technical": keywords.technical,
                "soft_skills": keywords.soft_skills,
                "domains": keywords.domains,
                "seniority": keywords.seniority,
            },
            "matching_inserted": inserted_matches,
            "formation_matching_inserted": inserted_formations,
        }

    def _match_experiences_and_projects(self, offer_id: str, keywords: OfferKeywords) -> int:
        inserted = 0
        offer_terms = {term.lower() for term in keywords.technical + keywords.domains + keywords.soft_skills}

        for exp in self.repo.fetch_experiences():
            exp_terms = set(_json_list(exp.get("skills_json")))
            exp_terms.update(_tokens(str(exp.get("role", ""))))
            exp_terms.update(_tokens(str(exp.get("description", ""))))
            score = _jaccard_score(offer_terms, exp_terms)
            if score > 0:
                self.repo.insert_matching_score(
                    offer_id=offer_id,
                    match_type="experience",
                    exp_id=str(exp["exp_id"]),
                    project_id=None,
                    score=score,
                    reasoning="Heuristic overlap between offer keywords and experience profile.",
                    model_version=self.config.model_version,
                )
                inserted += 1

        for project in self.repo.fetch_projects():
            project_terms = set(_json_list(project.get("languages_json")))
            project_terms.update(_json_list(project.get("technologies_json")))
            project_terms.update(_tokens(str(project.get("description", ""))))
            score = _jaccard_score(offer_terms, project_terms)
            if score > 0:
                self.repo.insert_matching_score(
                    offer_id=offer_id,
                    match_type="project",
                    exp_id=None,
                    project_id=str(project["project_id"]),
                    score=score,
                    reasoning="Heuristic overlap between offer keywords and project technologies.",
                    model_version=self.config.model_version,
                )
                inserted += 1

        return inserted

    def _match_formations(self, offer_id: str, keywords: OfferKeywords) -> int:
        inserted = 0
        offer_terms = {term.lower() for term in keywords.technical + keywords.domains + keywords.soft_skills}

        for formation in self.repo.fetch_formations():
            formation_terms = set(_json_list(formation.get("courses_json")))
            categories = _json_dict_keys_and_values(formation.get("course_categories_json"))
            formation_terms.update(categories)
            formation_terms.update(_tokens(str(formation.get("program", ""))))

            score = _jaccard_score(offer_terms, formation_terms)
            if score > 0:
                self.repo.insert_formation_matching_score(
                    offer_id=offer_id,
                    formation_id=str(formation["formation_id"]),
                    score=score,
                    reasoning="Heuristic overlap between offer keywords and formation courses.",
                    model_version=self.config.model_version,
                )
                inserted += 1

        return inserted


def _tokens(text: str) -> set[str]:
    return {token.strip(" ,.;:!?()[]{}\"'").lower() for token in text.split() if token.strip()}


def _json_list(raw: Any) -> list[str]:
    try:
        data = json.loads(raw) if isinstance(raw, str) else []
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [str(item).lower() for item in data]


def _json_dict_keys_and_values(raw: Any) -> set[str]:
    try:
        data = json.loads(raw) if isinstance(raw, str) else {}
    except json.JSONDecodeError:
        return set()
    if not isinstance(data, dict):
        return set()

    values: set[str] = set()
    for key, value in data.items():
        values.add(str(key).lower())
        if isinstance(value, list):
            for item in value:
                values.add(str(item).lower())
    return values


def _jaccard_score(offer_terms: set[str], profile_terms: set[str]) -> float:
    if not offer_terms or not profile_terms:
        return 0.0
    intersection = offer_terms.intersection(profile_terms)
    union = offer_terms.union(profile_terms)
    return round(len(intersection) / len(union), 4)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract keywords and compute matching for one offer")
    parser.add_argument("offer_id", help="Offer identifier present in offers_raw")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    args = _build_parser().parse_args(argv)

    root = Path(__file__).resolve().parents[2]
    config = OrchestrationConfig.from_repo_root(root)
    orchestrator = OfferLLMOrchestrator(config)
    result = orchestrator.run(args.offer_id)
    LOGGER.info("Matching result: %s", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
