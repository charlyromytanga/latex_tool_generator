"""Thank-you letter channel."""

from __future__ import annotations

from pathlib import Path

from .base import ChannelContext, ChannelResult, OutputChannel


class ThankYouLetterChannel(OutputChannel):
    """Generates a simple thank-you letter artifact."""

    channel_type = "thank_you"

    def generate(self, context: ChannelContext, output_dir: Path) -> ChannelResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / f"thank_you_{context.offer_id}.txt"
        artifact_path.write_text(
            (
                f"Thank you note for {context.company_name}\n"
                f"Offer: {context.offer_id}\n"
                f"Language: {context.language}\n"
            ),
            encoding="utf-8",
        )
        return self._build_result(self.channel_type, artifact_path)
