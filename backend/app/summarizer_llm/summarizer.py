"""Summarization Logic."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import mlflow
import yaml
from prefect import task

mlflow.set_experiment("summarizer-experiments")

class LLMClient:
    """Client for interacting with LLM summarization API."""

    def __init__(self, config_path: str = "llm_config.yaml") -> None:
        """Initialize LLMClient with configuration from a YAML file."""
        config_path = Path(config_path)
        with config_path.open("r") as f:
            config = yaml.safe_load(f)
        self.api_url = config["ollama_host"] + "/api/generate"
        self.model = config["model_name"]
        self.prompt_template = config["prompt_template"]

    @task(name="Summarize Text")
    async def summarize(self, text: str) -> str:
        """Summarize the provided text using the LLM API."""
        prompt = self.prompt_template.replace("{input}", text)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(self.api_url, json=payload)
            response.raise_for_status()
            summary = response.json()["response"]

            # Log to MLflow
            with mlflow.start_run(run_name=f"suggest_solution_{datetime.now(UTC).isoformat()}"):
                mlflow.log_param("model", self.model)
                mlflow.log_param("input_length", len(text))
                mlflow.log_param("output_length", len(summary))
                mlflow.set_tag("task", "summarization")
                mlflow.log_text(summary, "output.txt")

            return summary
