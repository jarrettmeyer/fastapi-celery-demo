#!/usr/bin/env bash

celery -A src.worker flower
