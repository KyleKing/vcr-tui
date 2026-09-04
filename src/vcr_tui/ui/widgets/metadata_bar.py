# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Widget showing the selected key's metadata as one summary line."""

from typing import Any

from textual.widgets import Static


class MetadataBarWidget(Static):
    """Static bar rendering the preview metadata key/value pairs."""

    def set_metadata(self, metadata: dict[str, Any]) -> None:
        """Render the metadata pairs, or blank when there are none."""
        if metadata:
            parts = [f'{k}: {v}' for k, v in metadata.items()]
            self.update(' | '.join(parts))
        else:
            self.update('')

    def clear_metadata(self) -> None:
        """Empty the bar."""
        self.update('')
