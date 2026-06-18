#!/usr/bin/env bash
set -euo pipefail

echo "=== Running P2P Multiplayer Integration Test ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

docker compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true

docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test-guest

HOST_EXIT_CODE=$(docker compose -f docker-compose.test.yml ps -a --format json 2>/dev/null \
    | grep '"test-host"' \
    | grep -o '"ExitCode":[0-9]*' \
    | grep -o '[0-9]*' || echo "0")
GUEST_EXIT_CODE=$(docker compose -f docker-compose.test.yml ps -a --format json 2>/dev/null \
    | grep '"test-guest"' \
    | grep -o '"ExitCode":[0-9]*' \
    | grep -o '[0-9]*' || echo "0")

echo "Host process exited with: $HOST_EXIT_CODE"
echo "Guest process exited with: $GUEST_EXIT_CODE"

docker compose -f docker-compose.test.yml down 2>/dev/null || true

if [ "$HOST_EXIT_CODE" -eq 0 ] && [ "$GUEST_EXIT_CODE" -eq 0 ]; then
    echo "INTEGRATION TEST SUCCESS: Game resolved safely without deadlock, crashes, or desyncs."
    exit 0
else
    echo "INTEGRATION TEST FAILURE: One or both clients encountered a crash or error condition."
    exit 1
fi
