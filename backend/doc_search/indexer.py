"""Index Docs."""

import time
from pathlib import Path

import hnswlib
import mlflow
import numpy as np
import yaml

from backend.doc_search.embedder import Embedder

mlflow.set_experiment("indexing-experiments")


def mlflow_log_indexing(func): # noqa: ANN001,ANN201
    """Log indexes."""
    def wrapper(self, *args, **kwargs):  # noqa: ANN001,ANN003,ANN002,ANN202
        with mlflow.start_run(run_name=f"Indexing_{self.folder.name}"):
            mlflow.log_param("embedding_model", self.embedder.model.__class__.__name__)
            mlflow.log_param("folder", str(self.folder))
            start_time = time.time()
            result = func(self, *args, **kwargs)
            mlflow.log_metric("num_documents", len(self.docs))
            mlflow.log_metric("indexing_time_sec", time.time() - start_time)
            return result
    return wrapper


class TranscriptIndex:
    """Initialize and manage document index for transcript search."""

    def __init__(self, sug_type: int, config_path: str = "backend/config.yaml") -> None:
        """Initialize the index with folder and embedder setup."""
        config_path = Path(config_path)
        with config_path.open() as f:
            config = yaml.safe_load(f)
        self.folder = Path(config["knowledge_base"]) if sug_type == 0 else Path(config["transcript_folder"])
        self.embedder = Embedder(config_path)
        self.dim = 384
        self.index = hnswlib.Index(space="cosine", dim=self.dim)
        self.docs: list[dict[str, str]] = []

    @mlflow_log_indexing
    def load(self) -> None:
        """Load documents and build the HNSW index."""
        all_embeddings = []
        for file_path in self.folder.glob("*.md"):
            content = file_path.read_text()
            vec = self.embedder.embed(content)[0]
            all_embeddings.append(vec)
            self.docs.append({"content": content, "file": file_path.name})

        num_elements = len(all_embeddings)
        self.index.init_index(max_elements=num_elements, ef_construction=200, M=16)
        self.index.add_items(np.array(all_embeddings), ids=list(range(num_elements)))
        self.index.set_ef(50)

    def search(self, query: str, top_k: int = 1) -> list[dict[str, str]]:
        """Search for top_k most similar documents to the query."""
        q_vec = self.embedder.embed(query)[0]
        labels, _ = self.index.knn_query(q_vec, k=top_k)
        return [self.docs[i] for i in labels[0]]
