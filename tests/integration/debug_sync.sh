#!/usr/bin/env bash
# =============================================================================
# Debug sync: runs the network protocol step by step.
# Shows exactly where the handshake stops working.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Build fresh
cd "$PROJECT_DIR"
docker compose -f docker-compose.integration.yml down -v --remove-orphans 2>/dev/null || true
docker compose -f docker-compose.integration.yml build --no-cache 2>&1 | tail -2

# Start host in background  
docker compose -f docker-compose.integration.yml up -d host
echo "Waiting for host to start..."
sleep 3

# Try connecting from guest container
echo ""
echo "=== Guest connecting to host ==="
GUEST_LOG=$(docker compose -f docker-compose.integration.yml run --rm guest bash -c '
  timeout 30 uv run python -c "
import logging, time
logging.basicConfig(level=logging.DEBUG, format=\"%(levelname)s:%(name)s:%(message)s\")
from triple_triad.network.connection import P2PConnection, perform_handshake
from triple_triad.network.protocol import DEFAULT_PORT, HANDSHAKE_TIMEOUT_S

print(\"=== STEP 1: connect ===\")
conn = P2PConnection(player_name=\"DBG\")
result = conn.connect(\"172.28.0.10\", DEFAULT_PORT, timeout=5.0)
print(f\"connect() -> {result}\")
if not result:
    exit(1)

print(\"=== STEP 2: handshake ===\")
payload = perform_handshake(conn, timeout=HANDSHAKE_TIMEOUT_S)
print(f\"handshake -> {payload}\")
if payload is None:
    exit(2)

print(\"=== STEP 3: wait for SYNC_SETUP ===\")
# Host will send this after host_game_ui exits and lobby_sync runs
# But in headless test, host already picks rules and sends immediately
# We just wait up to 10s
packet = conn.queue_get_filtered(
    {\"SYNC_SETUP\", \"SYNC_ERROR\", \"CONNECTION_LOST\"},
    timeout=10.0,
)
if packet is None:
    print(\"RESULT: timeout waiting for SYNC_SETUP\")
    exit(3)
msg_type = packet.get(\"type\", \"?\")
print(f\"Received packet type: {msg_type}\")
if msg_type != \"SYNC_SETUP\":
    print(f\"RESULT: expected SYNC_SETUP, got {msg_type}\")
    payload = packet.get(\"payload\", {})
    print(f\"Payload: {payload}\")
    exit(4)

print(\"=== STEP 4: sync succeeded! ===\")
payload = packet.get(\"payload\", {})
print(f\"Rules: {payload.get(\"rules\")}\")
print(f\"First turn: {payload.get(\"first_turn\")}\")
" 2>&1
' 2>&1 | grep -v "^Downloading\|^Installed\|^ Downloaded\|DD:\| " | head -30
)

echo "$GUEST_LOG"

docker compose -f docker-compose.integration.yml down -v --remove-orphans 2>/dev/null || true
