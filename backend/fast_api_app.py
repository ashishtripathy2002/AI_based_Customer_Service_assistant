"""Fast API doc search."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from backend.doc_search import index_docs, index_trans
from backend.workflows.pipeline import indexing_flow


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]: # noqa: ARG001
    """Run Prefect flow at app startup."""
    indexing_flow()
    yield


app = FastAPI(lifespan=lifespan)


class SearchQuery(BaseModel):
    """Model for search query."""

    query: str
    top_k: int = 1


@app.post("/search")
def search_similar(query: SearchQuery, sug_type: int = 1) -> dict[str, list[dict[str, str]]]:
    """Search for similar documents or transcripts."""
    matches = (
        index_trans.search(query.query, top_k=query.top_k)
        if sug_type == 1
        else index_docs.search(query.query, top_k=query.top_k)
    )
    return {"matches": matches}


if __name__ == "__main__":
    uvicorn.run("backend.fastapi:app", host="0.0.0.0", port=8000, reload=True) # noqa: S104
