#!/usr/bin/env bash

TASK_ID=

while [[ $# -gt 0 ]]; do
    case "$1" in
        --id)
            TASK_ID="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

curl -X GET http://localhost:9001/tasks/$TASK_ID -H "Accept: application/json"
