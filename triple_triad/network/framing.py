from __future__ import annotations

import json
import logging
import socket
import struct
from typing import Any

from .protocol import MAX_PACKET_SIZE

logger = logging.getLogger(__name__)


def send_packet(sock: socket.socket, data: dict[str, Any]) -> None:
    payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
    header = struct.pack("!I", len(payload))
    sock.sendall(header + payload)


def read_packet(sock: socket.socket) -> dict[str, Any] | None:
    header = recv_exact(sock, 4)
    if header is None:
        return None
    length = struct.unpack("!I", header)[0]
    if length == 0 or length > MAX_PACKET_SIZE:
        logger.warning("Receiver: invalid packet length %d", length)
        return None
    body = recv_exact(sock, length)
    if body is None:
        return None
    try:
        return json.loads(body.decode("utf-8"))  # type: ignore[no-any-return]
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning("Failed to decode packet body")
        return None


def recv_exact(sock: socket.socket, n: int) -> bytes | None:
    """Read exactly n bytes from socket, returning None on disconnect."""
    buf = bytearray()
    while len(buf) < n:
        try:
            chunk = sock.recv(n - len(buf))
        except TimeoutError:
            continue
        except (OSError, ConnectionResetError):
            return None
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)
