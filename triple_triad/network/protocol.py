from __future__ import annotations

from typing import Any

PROTOCOL_VERSION = 1
HEARTBEAT_INTERVAL_S = 5.0
HEARTBEAT_TIMEOUT_S = 30.0
HANDSHAKE_TIMEOUT_S = 10.0
MOVE_TIMEOUT_S = 120.0
DEFAULT_PORT = 64000
MAX_PACKET_SIZE = 100 * 1024  # 100 KB


class MessageType:
    HANDSHAKE = "HANDSHAKE"
    SYNC_SETUP = "SYNC_SETUP"
    SYNC_ACK = "SYNC_ACK"
    SYNC_ERROR = "SYNC_ERROR"
    DECK_SHARE = "DECK_SHARE"
    GAME_START = "GAME_START"
    GAME_START_ACK = "GAME_START_ACK"
    MOVE = "MOVE"
    FORFEIT = "FORFEIT"
    DISCONNECT = "DISCONNECT"
    HEARTBEAT_PING = "HEARTBEAT_PING"
    HEARTBEAT_PONG = "HEARTBEAT_PONG"
    CONNECTION_LOST = "CONNECTION_LOST"


def make_packet(msg_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"type": msg_type, "payload": payload or {}}


def parse_packet(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    msg_type = data.get("type", "")
    payload = data.get("payload", {})
    if not isinstance(payload, dict):
        payload = {}
    return msg_type, payload


# ── Packet constructors ──────────────────────────────────────────────────────


def make_handshake(player_name: str, version: int = PROTOCOL_VERSION) -> dict[str, Any]:
    return make_packet(
        MessageType.HANDSHAKE,
        {
            "version": version,
            "player_name": player_name,
        },
    )


def make_sync_setup(
    rules: list[str],
    board_elements: list[str | None],
    first_turn: str,
) -> dict[str, Any]:
    return make_packet(
        MessageType.SYNC_SETUP,
        {
            "rules": rules,
            "board_elements": board_elements,
            "first_turn": first_turn,
        },
    )


def make_deck_share(card_names: list[str]) -> dict[str, Any]:
    return make_packet(MessageType.DECK_SHARE, {"card_names": card_names})


def make_sync_error(reason: str = "") -> dict[str, Any]:
    return make_packet(MessageType.SYNC_ERROR, {"reason": reason})


def make_sync_ack() -> dict[str, Any]:
    return make_packet(MessageType.SYNC_ACK)


def make_game_start() -> dict[str, Any]:
    return make_packet(MessageType.GAME_START)


def make_game_start_ack() -> dict[str, Any]:
    return make_packet(MessageType.GAME_START_ACK)


def make_move(card_idx: int, position: int) -> dict[str, Any]:
    return make_packet(MessageType.MOVE, {"card_idx": card_idx, "position": position})


def make_forfeit(reason: str = "") -> dict[str, Any]:
    return make_packet(MessageType.FORFEIT, {"reason": reason})


def make_disconnect(reason: str = "") -> dict[str, Any]:
    return make_packet(MessageType.DISCONNECT, {"reason": reason})


def make_heartbeat_ping() -> dict[str, Any]:
    return make_packet(MessageType.HEARTBEAT_PING)


def make_heartbeat_pong() -> dict[str, Any]:
    return make_packet(MessageType.HEARTBEAT_PONG)
