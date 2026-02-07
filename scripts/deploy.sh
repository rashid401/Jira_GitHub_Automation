#!/bin/bash

set -e

APP_DIR="/opt/jira-github-automation"

cd "$APP_DIR"

if command -v docker-compose > /dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  COMPOSE_CMD="docker compose"
fi

$COMPOSE_CMD pull
$COMPOSE_CMD down || true
$COMPOSE_CMD up -d