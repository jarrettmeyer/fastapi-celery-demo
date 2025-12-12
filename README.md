# FastAPI + Celery Demo

A demonstration of FastAPI with Celery background tasks, Redis message broker, and Flower monitoring.

## Features

- FastAPI REST API with async support
- Celery distributed task queue
- Redis as message broker and result backend
- Flower for Celery monitoring
- Real-time WebSocket updates
- Simple web UI for task management
- Docker Compose for easy deployment

## Architecture

- **API Service** (Port 8000): FastAPI application serving REST API and web UI
- **Worker Service**: Celery worker processing background tasks
- **Flower Service** (Port 5555): Celery monitoring dashboard
- **Redis Service** (Port 6379): Message broker and result backend

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone the repository
2. Run with Docker Compose:

```bash
docker-compose up --build
```

3. Access the services:
   - Web UI: http://localhost:8000
   - Flower Dashboard: http://localhost:5555
   - API Docs: http://localhost:8000/docs

## API Endpoints

- `GET /` - Web UI
- `GET /health` - Health check
- `POST /tasks` - Create new task
- `GET /tasks/{task_id}` - Get task status
- `DELETE /tasks/{task_id}` - Cancel task
- `WS /tasks/{task_id}/ws` - WebSocket for real-time updates

## Development

### Using uv for local development:

```bash
# Install uv
pip install uv

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r pyproject.toml

# Run services locally
export REDIS_URL=redis://localhost:6379/0

# Terminal 1: Redis
docker run -p 6379:6379 redis:8-alpine

# Terminal 2: Celery worker
celery -A src.worker worker --loglevel=INFO

# Terminal 3: FastAPI
fastapi dev src/api.py

# Terminal 4: Flower (optional)
celery -A src.worker flower
```

## Environment Variables

- `REDIS_URL` - Redis connection URL (default: `redis://localhost:6379/0`)
- `DEBUG` - Enable debug mode (default: `true`)

## Project Structure

```
fastapi-celery-demo/
├── Dockerfile              # Multi-purpose Docker image
├── docker-compose.yaml     # Service orchestration
├── pyproject.toml          # Python dependencies
└── src/
    ├── api.py              # FastAPI application
    ├── worker.py           # Celery worker and tasks
    ├── config.py           # Configuration
    ├── models.py           # Pydantic models
    └── templates/
        └── index.html      # Web UI
```

## License

MIT