"""Recruiter email channel."""

from __future__ import annotations

from pathlib import Path

from .base import ChannelContext, ChannelResult, OutputChannel


class RecruiterEmailChannel(OutputChannel):
    """Generates a recruiter email artifact."""

    channel_type = "email"

    def generate(self, context: ChannelContext, output_dir: Path) -> ChannelResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / f"recruiter_email_{context.offer_id}.txt"
        artifact_path.write_text(
            (
                f"Subject: Application follow-up - {context.company_name}\n\n"
                f"Hello,\n"
                f"I would like to follow up regarding offer {context.offer_id}.\n"
            ),
            encoding="utf-8",
        )
        return self._build_result(self.channel_type, artifact_path)
