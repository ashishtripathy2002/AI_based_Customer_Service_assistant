"""Evaluate conversations using an LLM and log results to MLflow."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import mlflow
import yaml
from prefect import task

# Load configuration
conf_path = Path("llm_config.yaml")
with conf_path.open("r") as file:
    config = yaml.safe_load(file)

LLM_API_URL = config["llm"]["api_url"]
MODEL_NAME = config["llm"]["model_name"]
BASE_PROMPT = config["llm"]["prompt"]

# Configure MLflow
mlflow.set_experiment("micro-skill-evaluation-experiments")


@task(name="Evaluate Micro Skills Conversation")
async def evaluate_conversation(conversation: str) -> str:
    """Evaluate a conversation and log metrics to MLflow."""
    full_prompt = f"{BASE_PROMPT}\n\nConversation:\n{conversation}"

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(LLM_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()["response"]

        run_name = f"ms_eval_{datetime.now(UTC).isoformat()}"
        with mlflow.start_run(run_name=run_name):
            mlflow.log_param("model", MODEL_NAME)
            mlflow.log_param("input_length", len(conversation))
            mlflow.log_param("output_length", len(result))
            mlflow.set_tag("task", "micro_skill_evaluation")
            mlflow.log_text(result, "ms_eval_output.txt")

        return result
