"""YAML Loader and Validator for Semantic Layer."""

from __future__ import annotations

from pathlib import Path
import yaml

from src.core.config import settings
from src.core.exceptions import SemanticResolutionError
from src.semantic.models import SemanticLayerConfig


class SemanticLayerLoader:
    """Loads and validates semantic_layer.yaml."""

    def __init__(self, config_path: Path | str | None = None):
        self.config_path = Path(config_path or (settings.config_dir / "semantic_layer.yaml"))

    def load(self) -> SemanticLayerConfig:
        """Parse YAML file and validate against SemanticLayerConfig Pydantic model."""
        if not self.config_path.exists():
            raise SemanticResolutionError(f"Semantic layer config not found at: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
            return SemanticLayerConfig(**raw_data)
        except Exception as e:
            raise SemanticResolutionError(f"Failed to parse semantic_layer.yaml: {e}") from e
