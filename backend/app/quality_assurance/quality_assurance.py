"""FastAPI task for evaluating QA policy compliance using an external LLM and MLflow logging."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import mlflow
import yaml
from prefect import task

# Load YAML config
CONFIG_PATH = Path("config.yaml")
with CONFIG_PATH.open() as f:
    config = yaml.safe_load(f)

# Config values
OLLAMA_URL = config["ollama"]["base_url"]
MODEL = config["ollama"]["model"]
PROMPT_TEMPLATE = config["qa_policy"]["prompt"]

# Set MLflow Tracking
mlflow.set_experiment("qa-evaluation-experiments")


@task(name="Evaluate QA Response")
async def evaluate_response(agent_response: str) -> str:
    """Evaluate agent's response for QA policy compliance."""
    prompt = PROMPT_TEMPLATE.replace("{agent_response}", agent_response)
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        response.raise_for_status()
        result = response.json()["response"]

        # Log to MLflow
        with mlflow.start_run(run_name=f"qa_eval_{datetime.now(tz=UTC).isoformat()}"):
            mlflow.log_param("model", MODEL)
            mlflow.log_param("input_length", len(agent_response))
            mlflow.log_param("output_length", len(result))
            mlflow.set_tag("task", "qa_evaluation")
            mlflow.log_text(result, "evaluation.txt")

        return result
