"""Thesis channel."""

from __future__ import annotations

from pathlib import Path

from .base import ChannelContext, ChannelResult, OutputChannel


class ThesisChannel(OutputChannel):
    """Generates a thesis-like artifact."""

    channel_type = "thesis"

    def generate(self, context: ChannelContext, output_dir: Path) -> ChannelResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / f"thesis_{context.offer_id}.txt"
        artifact_path.write_text(
            (
                f"Thesis draft\n"
                f"Offer: {context.offer_id}\n"
                f"Company: {context.company_name}\n"
                f"Language: {context.language}\n"
            ),
            encoding="utf-8",
        )
        return self._build_result(self.channel_type, artifact_path)
