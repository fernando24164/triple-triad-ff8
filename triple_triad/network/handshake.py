from __future__ import annotations

from typing import Any

from .connection import P2PConnection
from .protocol import (
    HANDSHAKE_TIMEOUT_S,
    PROTOCOL_VERSION,
    MessageType,
    make_handshake,
    parse_packet,
)


def perform_handshake(
    conn: P2PConnection,
    timeout: float = HANDSHAKE_TIMEOUT_S,
) -> dict[str, Any] | None:
    """Start background threads, exchange handshakes, and validate protocol version.

    Returns the peer's handshake payload on success, None on failure
    (timeout, connection lost, or version mismatch).
    """
    conn.start_background()
    conn.send(make_handshake(conn.player_name))

    packet = conn.queue_get_filtered(
        {MessageType.HANDSHAKE, MessageType.CONNECTION_LOST},
        timeout=timeout,
    )
    if packet is None:
        return None

    msg_type, payload = parse_packet(packet)
    if msg_type == MessageType.CONNECTION_LOST:
        return None
    if payload.get("version") != PROTOCOL_VERSION:
        return None

    return payload
