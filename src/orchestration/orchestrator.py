"""Central orchestrator wiring Level 1 (ingest) and Level 2 (matching)."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Sequence

from .config import OrchestrationConfig
from .ingest import OfferIngestionOrchestrator
from .llm_extractors import OfferLLMOrchestrator


LOGGER = logging.getLogger(__name__)


class OfferPipelineOrchestrator:
    """Runs the end-to-end offer pipeline up to generation readiness."""

    def __init__(self, config: OrchestrationConfig) -> None:
        self.config = config
        self.ingest = OfferIngestionOrchestrator(config)
        self.llm = OfferLLMOrchestrator(config)

    def process_offer(self, offer_path: Path) -> dict[str, Any]:
        ingest_result = self.ingest.run_from_file(offer_path)
        offer_id = str(ingest_result["offer_id"])
        llm_result = self.llm.run(offer_id)

        recommendation = self._recommendation(llm_result)
        return {
            "status": "SUCCESS",
            "offer_id": offer_id,
            "ingestion": ingest_result,
            "matching": llm_result,
            "recommendation": recommendation,
        }

    def _recommendation(self, llm_result: dict[str, Any]) -> str:
        inserted = int(llm_result.get("matching_inserted", 0))
        if inserted <= 0:
            return "SKIP"
        if inserted < 3:
            return "REVIEW"
        return "GO_TO_LEVEL3"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run full offer pipeline (ingest + matching)")
    parser.add_argument("offer_path", type=Path, help="Path to markdown offer file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    args = _build_parser().parse_args(argv)

    root = Path(__file__).resolve().parents[2]
    config = OrchestrationConfig.from_repo_root(root)
    orchestrator = OfferPipelineOrchestrator(config)
    result = orchestrator.process_offer(args.offer_path)
    LOGGER.info("Pipeline result: %s", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
