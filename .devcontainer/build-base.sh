#!/usr/bin/env bash
set -e
echo "Building base image (5-10 minutes)..."
docker build -f .devcontainer/base.Dockerfile -t doc-translator-base:latest .
echo "Base image built successfully."
echo "Now run: docker compose up -d"