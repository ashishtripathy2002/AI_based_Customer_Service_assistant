"""Embedd transcripts/KB."""

from pathlib import Path

import numpy as np
import yaml
from sentence_transformers import SentenceTransformer


class Embedder:
    """Class to load and use a sentence transformer model for embedding texts."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize Embedder with configuration from a YAML file."""
        config_path = Path(config_path)
        with config_path.open() as f:
            config = yaml.safe_load(f)
        self.model = SentenceTransformer(config["embedding_model"])

    def embed(self, texts: str | list[str]) -> np.ndarray:
        """Embed the given texts using the loaded sentence transformer model."""
        if isinstance(texts, str):
            texts = [texts]
        return np.array(self.model.encode(texts, convert_to_numpy=True))
