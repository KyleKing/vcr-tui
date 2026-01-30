from typing import Any

from textual.widgets import Static


class MetadataBarWidget(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._metadata: dict[str, Any] = {}

    def set_metadata(self, metadata: dict[str, Any]) -> None:
        self._metadata = metadata
        if metadata:
            parts = [f"{k}: {v}" for k, v in metadata.items()]
            self.update(" | ".join(parts))
        else:
            self.update("")

    def clear_metadata(self) -> None:
        self._metadata = {}
        self.update("")
