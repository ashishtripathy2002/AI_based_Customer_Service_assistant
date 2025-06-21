FROM python:3.12-slim

# Install uv by copying the executables
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy code and config
COPY . .

# Install dependencies using uv (MUCH faster than pip)
RUN uv sync

EXPOSE 8002

CMD ["uv","run","uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
