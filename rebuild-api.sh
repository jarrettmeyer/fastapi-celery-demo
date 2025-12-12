#!/usr/bin/env bash

podman stop api
podman rm api
podman compose build api
podman compose up --detach api
