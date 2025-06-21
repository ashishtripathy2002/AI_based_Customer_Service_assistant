"""Micro-skill evaluation FastAPI application."""

from fastapi import FastAPI
from prefect import flow
from pydantic import BaseModel

from ms_advance import evaluate_conversation

app = FastAPI(title="Micro-Skill Evaluation", version="1.0")


class InputData(BaseModel):
    """Request body model for conversation input."""

    conversation: str


@flow(name="MicroSkill Evaluation Flow")
async def run_micro_skill_eval(convo: str) -> str:
    """Run micro-skill evaluation."""
    return await evaluate_conversation.fn(convo)


@app.post("/ms-advance")
async def micro_skill_endpoint(data: InputData) -> dict[str, str]:
    """Evaluate micro-skills endpoint."""
    result = await run_micro_skill_eval(data.conversation)
    return {"evaluation": result}
