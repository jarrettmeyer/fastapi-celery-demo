FROM python:3.13-alpine

WORKDIR /opt/fastapi-celery-demo

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip
RUN pip install uv

COPY ./ ./

RUN uv sync
