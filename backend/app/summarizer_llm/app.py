"""Summarization API."""

import traceback

from fastapi import FastAPI, HTTPException
from prefect import flow
from pydantic import BaseModel
from summarizer import LLMClient

app = FastAPI(title="LLaMA3 Summarization Service", version="1.0")
summarizer = LLMClient()

class SummarizationRequest(BaseModel):
    """Request body for summarization."""

    text: str

@flow(name="Summarization Flow")
async def run_summarization(text: str) -> str:
    """Run the summarization flow."""
    return await summarizer.summarize.fn(summarizer, text)

@app.post("/summarize")
async def summarize_text(req: SummarizationRequest) -> dict:
    """Handle the summarization request."""
    try:
        result = await run_summarization(req.text)
    except HTTPException:
        traceback.print_exc()
    else:
        return {"result": result}
