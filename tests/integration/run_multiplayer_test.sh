#!/usr/bin/env bash
# =============================================================================
# Triple Triad - Multiplayer Integration Test Runner
# =============================================================================
# Runs two Docker containers (host + guest) that play a full headless P2P game.
# Exits 0 if both containers finish cleanly.
#
# Usage:
#   ./run_multiplayer_test.sh              # Run (uses cache)
#   ./run_multiplayer_test.sh --build      # Force rebuild images
#   ./run_multiplayer_test.sh --verbose    # Show live container logs
#   ./run_multiplayer_test.sh --clean      # Nuke everything first
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.integration.yml"

VERBOSE=false
BUILD_FLAG=""

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
log()   { echo -e "${CYAN}[test]${NC} $*"; }
ok()    { echo -e "${GREEN}[PASS]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; }

cleanup() {
    docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
}
trap cleanup EXIT

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build)    BUILD_FLAG="--build"; shift ;;
        --verbose)  VERBOSE=true; shift ;;
        --clean)    docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true; shift ;;
        *)          echo "Usage: $0 [--build] [--verbose] [--clean]"; exit 1 ;;
    esac
done

echo -e "\n${BOLD}═══ Triple Triad - P2P Multiplayer Integration Test ═══${NC}\n"

# Build + run in one shot
UP=(docker compose -f "$COMPOSE_FILE" up)
[ -n "$BUILD_FLAG" ] && UP+=(--build)
UP+=(--abort-on-container-exit --exit-code-from guest)

if $VERBOSE; then
    "${UP[@]}"
else
    "${UP[@]}" 2>&1 | tail -40
fi

# Collect results
HOST_EXIT=$(docker inspect --format='{{.State.ExitCode}}' tt-integration-host 2>/dev/null || echo "-1")
GUEST_EXIT=$(docker inspect --format='{{.State.ExitCode}}' tt-integration-guest 2>/dev/null || echo "-1")

echo ""
log "Host exit:  $HOST_EXIT"
log "Guest exit: $GUEST_EXIT"

echo ""
log "── Host logs ──"
docker logs tt-integration-host 2>&1 | tail -15
echo ""
log "── Guest logs ──"
docker logs tt-integration-guest 2>&1 | tail -15

echo ""
if [ "$HOST_EXIT" = "0" ] && [ "$GUEST_EXIT" = "0" ]; then
    ok "Both containers exited cleanly."
    exit 0
else
    fail "Host=$HOST_EXIT  Guest=$GUEST_EXIT"
    exit 1
fi
