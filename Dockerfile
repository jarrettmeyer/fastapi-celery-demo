FROM python:3.13-alpine

WORKDIR /opt/fastapi-celery-demo

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/fastapi-celery-demo/.venv/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install uv

COPY ./ ./

RUN uv sync

ENTRYPOINT []

CMD ["fastapi", "run", "src/api.py", "--host", "0.0.0.0", "--port", "9001"]
