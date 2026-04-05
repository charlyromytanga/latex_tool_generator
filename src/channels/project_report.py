"""Project report channel."""

from __future__ import annotations

from pathlib import Path

from .base import ChannelContext, ChannelResult, OutputChannel


class ProjectReportChannel(OutputChannel):
    """Generates a project report artifact."""

    channel_type = "report"

    def generate(self, context: ChannelContext, output_dir: Path) -> ChannelResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / f"project_report_{context.offer_id}.txt"
        artifact_path.write_text(
            (
                f"Project report\n"
                f"Offer: {context.offer_id}\n"
                f"Company: {context.company_name}\n"
                f"Payload keys: {sorted(context.payload.keys())}\n"
            ),
            encoding="utf-8",
        )
        return self._build_result(self.channel_type, artifact_path)
