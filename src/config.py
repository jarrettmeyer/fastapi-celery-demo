from celery import states
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Redis configuration
    redis_url: str = "redis://localhost:6379/0"

    # Application configuration
    debug: bool = True

    # Celery configuration
    celery_result_expires: int = 3600
    celery_result_extended: bool = True
    celery_task_track_started: bool = True
    celery_task_send_sent_event: bool = True

    # Worker configuration
    worker_max_timeout: int = 180

    # Task listing configuration
    inspect_timeout: float = 1.0

    # Task states - use Celery's READY_STATES for terminal states
    terminal_states: list[str] = list(states.READY_STATES)

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
