"""Base contract for output channels."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChannelContext:
    """Common input payload used by channel generators."""

    offer_id: str
    company_name: str
    language: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ChannelResult:
    """Result metadata for generated channel artifacts."""

    channel_type: str
    artifact_path: str
    generated_at: str


class OutputChannel(ABC):
    """Abstract base class for all Level 3 output channels."""

    channel_type: str

    @abstractmethod
    def generate(self, context: ChannelContext, output_dir: Path) -> ChannelResult:
        """Generate one channel artifact and return output metadata."""

    @staticmethod
    def _build_result(channel_type: str, artifact_path: Path) -> ChannelResult:
        return ChannelResult(
            channel_type=channel_type,
            artifact_path=str(artifact_path),
            generated_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        )
