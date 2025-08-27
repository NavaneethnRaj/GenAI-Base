# Base image with uv and Python
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Copy dependency files first (for layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen --no-cache

# Copy project files
COPY . .

# Expose FastAPI port
EXPOSE 8668

# Run the app with uvicorn
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8668", "--reload"]