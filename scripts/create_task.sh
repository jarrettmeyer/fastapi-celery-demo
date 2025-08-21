#!/usr/bin/env bash

DURATION=30

while [[ $# -gt 0 ]]; do
    case "$1" in
        --duration)
            DURATION="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

curl -X POST http://localhost:9001/tasks \
    -H "Content-type: application/json" \
    -H "Accept: application/json" \
    -d "{\"duration\": $DURATION}"
