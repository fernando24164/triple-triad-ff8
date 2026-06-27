#!/usr/bin/env bash
# =============================================================================
# Triple Triad - Interactive Multiplayer (2 Docker Containers)
# =============================================================================
# Starts two containers on a private network and prints the commands you need
# to open two terminals and play against yourself over the network.
#
# Usage:
#   ./play_interactive.sh              # Build (if needed) and start
#   ./play_interactive.sh --build      # Force rebuild images
#   ./play_interactive.sh --debug      # Start guest with debugpy (wait for Zed)
#   ./play_interactive.sh --clean      # Tear down and exit
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.interactive.yml"

BUILD_FLAG=""
DEBUG_MODE=false

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

cleanup() {
    echo ""
    echo -e "${CYAN}[play]${NC} Tearing down containers..."
    docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build)   BUILD_FLAG="--build"; shift ;;
        --debug)   DEBUG_MODE=true; shift ;;
        --clean)   docker compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null; echo "Cleaned."; exit 0 ;;
        *)         echo "Usage: $0 [--build] [--debug] [--clean]"; exit 1 ;;
    esac
done

echo -e "\n${BOLD}═══ Triple Triad - Interactive P2P Multiplayer ═══${NC}\n"

# Build + start
UP=(docker compose -f "$COMPOSE_FILE" up -d)
[ -n "$BUILD_FLAG" ] && UP+=(--build)

echo -e "${CYAN}[play]${NC} Starting containers..."
"${UP[@]}"

echo ""
echo -e "${GREEN}Containers are running.${NC}"

if [ "$DEBUG_MODE" = true ]; then
    echo ""
    echo -e "${CYAN}[play]${NC} Starting guest with debugpy (waiting for Zed to attach)..."
    docker exec -d tt-play-guest uv run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m triple_triad
    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║  DEBUG MODE                                                  ║${NC}"
    echo -e "${BOLD}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}║                                                              ║${NC}"
    echo -e "${BOLD}║  Guest is waiting for debugger on port 5678.                 ║${NC}"
    echo -e "${BOLD}║                                                              ║${NC}"
    echo -e "${BOLD}║  In Zed:                                                     ║${NC}"
    echo -e "${CYAN}║    1. Set breakpoints in triple_triad/ source files          ║${NC}"
    echo -e "${CYAN}║    2. Press F4                                               ║${NC}"
    echo -e "${CYAN}║    3. Select 'Attach to Guest Container'                     ║${NC}"
    echo -e "${BOLD}║                                                              ║${NC}"
    echo -e "${BOLD}║  TERMINAL 1 (Host - for playing):                            ║${NC}"
    echo -e "${CYAN}║    docker exec -it tt-play-host bash                         ║${NC}"
    echo -e "${DIM} ║    # then inside the container:                              ║${NC}"
    echo -e "${CYAN}║    uv run python -m triple_triad                             ║${NC}"
    echo -e "${DIM} ║    # navigate: New Game > Multiplayer > Host Game            ║${NC}"
    echo -e "${BOLD}║                                                              ║${NC}"
    echo -e "${BOLD}║  To exit containers: close both terminals, then run:         ║${NC}"
    echo -e "${CYAN}║    ./play_interactive.sh --clean                             ║${NC}"
    echo -e "${BOLD}║                                                              ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}"
else
    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║  HOW TO PLAY                                                 ║${NC}"
    echo -e "${BOLD}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}║                                                              ║${NC}"
    echo -e "${BOLD}║  Open TWO separate terminals and run these commands:         ║${NC}"
    echo -e "${BOLD}║                                                              ║${NC}"
    echo -e "${BOLD}║  TERMINAL 1 (Host):                                          ║${NC}"
    echo -e "${CYAN}║    docker exec -it tt-play-host bash                         ║${NC}"
    echo -e "${DIM} ║    # then inside the container:                              ║${NC}"
    echo -e "${CYAN}║    uv run python -m triple_triad                             ║${NC}"
    echo -e "${DIM} ║    # navigate: New Game > Multiplayer > Host Game            ║${NC}"
    echo -e "${DIM} ║    # wait for guest to connect                               ║${NC}"
    echo -e "${BOLD}║                                                              ║${NC}"
    echo -e "${BOLD}║  TERMINAL 2 (Guest):                                         ║${NC}"
    echo -e "${CYAN}║    docker exec -it tt-play-guest bash                        ║${NC}"
    echo -e "${DIM} ║    # then inside the container:                              ║${NC}"
    echo -e "${CYAN}║    uv run python -m triple_triad                             ║${NC}"
    echo -e "${DIM} ║    # navigate: New Game > Multiplayer > Join Game            ║${NC}"
    echo -e "${DIM} ║    # enter IP: 172.29.0.10  port: 64000                      ║${NC}"
    echo -e "${BOLD}║                                                              ║${NC}"
    echo -e "${BOLD}║  To exit containers: close both terminals, then run:         ║${NC}"
    echo -e "${CYAN}║    ./play_interactive.sh --clean                             ║${NC}"
    echo -e "${BOLD}║                                                              ║${NC}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}"
fi
echo ""
echo -e "${DIM}Press Ctrl+C here to stop both containers.${NC}"

trap cleanup INT TERM

# Keep script alive so Ctrl+C triggers cleanup
while true; do
    sleep 10
    # Check if containers are still running
    if ! docker inspect tt-play-host >/dev/null 2>&1; then
        echo -e "\n${RED}[play]${NC} Host container stopped unexpectedly."
        docker logs tt-play-host --tail 10 2>&1 || true
        break
    fi
    if ! docker inspect tt-play-guest >/dev/null 2>&1; then
        echo -e "\n${RED}[play]${NC} Guest container stopped unexpectedly."
        docker logs tt-play-guest --tail 10 2>&1 || true
        break
    fi
done
