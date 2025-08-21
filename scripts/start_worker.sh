#!/usr/bin/env bash

celery -A src.worker worker --concurrency=10 --loglevel=INFO
