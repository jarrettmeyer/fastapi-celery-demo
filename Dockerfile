FROM python:3.13-slim

WORKDIR /opt/app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/app/.venv/bin:$PATH"

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv
RUN uv venv /opt/app/.venv && \
    uv pip install -r pyproject.toml

# Copy application code
COPY src/ ./src/

# Expose ports (for documentation, actual ports in docker-compose)
EXPOSE 8000 5555

CMD ["fastapi", "run", "src/api.py", "--host", "0.0.0.0", "--port", "8000"]
