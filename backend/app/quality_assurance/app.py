"""FastAPI service to evaluate QA policy compliance using Prefect and an external LLM."""

import traceback

from fastapi import FastAPI, HTTPException
from prefect import flow
from pydantic import BaseModel

from quality_assurance import evaluate_response

app = FastAPI(title="QA Policy Evaluation", version="1.0")

class QARequest(BaseModel):
    """Request body model for agent response input."""

    agent_response: str


@flow(name="QA Evaluation Flow")
async def run_evaluation(text: str) -> str:
    """Run the QA evaluation flow using Prefect."""
    return await evaluate_response.fn(text)


@app.post("/evaluate")
async def evaluate_qa(request: QARequest) -> dict[str, str]:
    """Evaluate an conversation and return policy compliance."""
    try:
        result = await run_evaluation(request.agent_response)
    except HTTPException:
        traceback.print_exc()
    else:
        return {"evaluation": result}
