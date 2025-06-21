"""Solution Suggestions Logic."""

from datetime import UTC, datetime
from pathlib import Path

import httpx
import mlflow
import yaml
from prefect import task

# Setup MLflow
mlflow.set_experiment("solution-suggester-experiments")

class SolutionSuggester:
    """Suggest solutions based on similar transcripts."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize SolutionSuggester with the given configuration path."""
        config_path = Path(config_path)
        with config_path.open() as f:
            config = yaml.safe_load(f)
        self.transcript_url = config["transcript_search_url"]
        self.ollama_url = config["ollama_host"] + "/api/generate"
        self.llm_model = config["llm_model"]
        self.prompt_template = config["prompt_template"]

    @task(name="Get Similar Transcripts")
    async def get_similar_transcripts(self, query: str, top_k: int = 1, sug_type: int = 1) -> list:
        """Fetch similar transcripts based on the query."""
        async with httpx.AsyncClient(timeout=1000) as client:
            response = await client.post(
                self.transcript_url,
                json={"query": query, "top_k": top_k},
                params={"type": sug_type},
            )
            response.raise_for_status()
            return response.json()["matches"]

    @task(name="Extract Suggested Solutions")
    async def extract_solutions(self, transcripts: list) -> str:
        """Extract solutions from the given transcripts using an LLM model."""
        joined = "\n\n---\n\n".join(f"Transcript:{t['content']}" for t in transcripts)
        prompt = self.prompt_template.replace("{input}", joined.replace("\n", " ").replace("\\", ""))
        async with httpx.AsyncClient(timeout=1000) as client:
            payload = {
                "model": self.llm_model,
                "prompt": prompt,
                "stream": False,
            }
            response = await client.post(self.ollama_url, json=payload)
            response.raise_for_status()
            summary = response.json()["response"]

            with mlflow.start_run(run_name=f"suggest_solution_{datetime.now(UTC).isoformat()}"):
                mlflow.log_param("model", self.llm_model)
                mlflow.log_param("transcript_count", len(transcripts))
                mlflow.log_param("input_chars", len(prompt))
                mlflow.log_param("output_chars", len(summary))
                mlflow.set_tag("task", "solution_suggestion")
                mlflow.log_text(summary, "suggested_solution.txt")

            return summary
