"""FastAPI service for suggesting solutions using Prefect and external Suggester."""

import traceback

from fastapi import FastAPI, HTTPException
from prefect import flow
from pydantic import BaseModel
from suggester import SolutionSuggester

app = FastAPI(title="Solution Suggestion Service", version="1.0")
suggester = SolutionSuggester()

class SuggestionRequest(BaseModel):
    """Request model for solution suggestion."""

    message: str
    top_k: int = 1
    sug_type: int = 1

@flow(name="Solution Suggestion Flow")
async def run_solution_suggestion(message: str, top_k: int = 1, sug_type: int = 1) -> str:
    """Run solution suggestion flow."""
    transcripts = await suggester.get_similar_transcripts.fn(suggester, message, top_k, sug_type)
    return await suggester.extract_solutions.fn(suggester, transcripts)

@app.post("/suggest_solution")
async def suggest_solution(req: SuggestionRequest) -> dict:
    """Endpoint to suggest a solution based on user message."""
    try:
        result = await run_solution_suggestion(req.message, req.top_k, req.sug_type)
    except HTTPException:
        traceback.print_exc()
    else:
        return {"suggested_solution": result}
