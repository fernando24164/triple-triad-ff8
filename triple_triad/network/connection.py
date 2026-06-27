from __future__ import annotations

import contextlib
import json
import logging
import queue
import socket
import struct
import threading
import time
from typing import Any

from .protocol import (
    HANDSHAKE_TIMEOUT_S,
    HEARTBEAT_INTERVAL_S,
    HEARTBEAT_TIMEOUT_S,
    MAX_PACKET_SIZE,
    PROTOCOL_VERSION,
    MessageType,
    make_disconnect,
    make_handshake,
    make_heartbeat_ping,
    make_heartbeat_pong,
    make_packet,
    parse_packet,
)

logger = logging.getLogger(__name__)


class P2PConnection:
    """Stateful TCP connection wrapper with background receiver thread."""

    def __init__(self, player_name: str = "Player") -> None:
        self.player_name = player_name
        self.sock: socket.socket | None = None
        self._server_sock: socket.socket | None = None
        self.incoming: queue.Queue[dict[str, Any]] = queue.Queue()
        self._running = False
        self._recv_thread: threading.Thread | None = None
        self._hb_thread: threading.Thread | None = None
        self._last_pong: float = 0.0
        self._pending: list[dict[str, Any]] = []
        self.is_host = False
        self.connected = False
        self.remote_name: str = ""
        self._send_lock = threading.Lock()

    # ── Socket framing ────────────────────────────────────────────────────────

    @staticmethod
    def send_packet(sock: socket.socket, data: dict[str, Any]) -> None:
        payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
        header = struct.pack("!I", len(payload))
        sock.sendall(header + payload)

    @staticmethod
    def read_packet(sock: socket.socket) -> dict[str, Any] | None:
        header = _recv_exact(sock, 4)
        if header is None:
            return None
        length = struct.unpack("!I", header)[0]
        if length == 0 or length > MAX_PACKET_SIZE:
            logger.warning("Receiver: invalid packet length %d", length)
            return None
        body = _recv_exact(sock, length)
        if body is None:
            return None
        try:
            return json.loads(body.decode("utf-8"))  # type: ignore[no-any-return]
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Failed to decode packet body")
            return None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def host(self, port: int) -> None:
        self.is_host = True
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(("", port))
        self._server_sock.listen(1)
        self._server_sock.settimeout(30.0)
        logger.info("Hosting on port %d", port)

    def accept(self, timeout: float | None = None) -> bool:
        assert self._server_sock is not None
        try:
            if timeout is not None:
                self._server_sock.settimeout(timeout)
            client, addr = self._server_sock.accept()
            client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            client.settimeout(None)
            self._close_server_socket()
            self.sock = client
            self.connected = True
            self._last_pong = time.monotonic()
            logger.info("Accepted connection from %s", addr)
            return True
        except (TimeoutError, OSError):
            return False

    def connect(self, host: str, port: int, timeout: float = 10.0) -> bool:
        self.is_host = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            self.sock.settimeout(timeout)
            self.sock.connect((host, port))
            self.sock.settimeout(None)  # reset to blocking mode
            self.connected = True
            self._last_pong = time.monotonic()
            logger.info("Connected to %s:%d", host, port)
            return True
        except (TimeoutError, OSError) as exc:
            logger.error("Connection failed: %s", exc)
            self._cleanup_socket()
            return False

    def start_background(self) -> None:
        self._running = True
        self._last_pong = time.monotonic()
        self._recv_thread = threading.Thread(
            target=self._receiver_loop, daemon=True, name="p2p-recv"
        )
        self._recv_thread.start()
        self._hb_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name="p2p-hb"
        )
        self._hb_thread.start()

    def stop(self) -> None:
        self._running = False
        self.connected = False
        self._cleanup_socket()

    def send(self, data: dict[str, Any]) -> None:
        if self.sock and self.connected:
            with self._send_lock:
                try:
                    self.send_packet(self.sock, data)
                except (BrokenPipeError, OSError) as exc:
                    logger.warning("Send failed: %s", exc)
                    self.connected = False
                    self.incoming.put(make_packet(MessageType.CONNECTION_LOST))

    def close(self) -> None:
        if self.connected:
            with contextlib.suppress(Exception):
                self.send(make_disconnect())
        self.stop()

    # ── Background loops ──────────────────────────────────────────────────────

    def _receiver_loop(self) -> None:
        logger.debug("Receiver loop started (sock=%s)", self.sock is not None)
        while self._running and self.sock:
            try:
                packet = self.read_packet(self.sock)
                if packet is None:
                    if self._running:
                        logger.warning(
                            "Receiver: read_packet returned None — connection lost"
                        )
                        self.incoming.put(make_packet(MessageType.CONNECTION_LOST))
                    break
                msg_type, _ = _parse_type(packet)
                if msg_type == MessageType.HEARTBEAT_PING:
                    self.send(make_heartbeat_pong())
                elif msg_type == MessageType.HEARTBEAT_PONG:
                    self._last_pong = time.monotonic()
                else:
                    self.incoming.put(packet)
            except (ConnectionResetError, BrokenPipeError, OSError) as exc:
                logger.warning("Receiver: exception — %s: %s", type(exc).__name__, exc)
                if self._running:
                    self.incoming.put(make_packet(MessageType.CONNECTION_LOST))
                break
        logger.debug("Receiver loop ended")

    def _heartbeat_loop(self) -> None:
        while self._running and self.connected:
            time.sleep(HEARTBEAT_INTERVAL_S)
            if not self._running or not self.connected:
                break
            self.send(make_heartbeat_ping())
            if not self.connected:
                break
            elapsed = time.monotonic() - self._last_pong
            if elapsed > HEARTBEAT_TIMEOUT_S:
                logger.warning("Heartbeat timeout (%.1fs)", elapsed)
                self.incoming.put(make_packet(MessageType.CONNECTION_LOST))
                break

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _close_server_socket(self) -> None:
        """Close only the listening server socket (if any)."""
        if self._server_sock:
            with contextlib.suppress(OSError):
                self._server_sock.close()
            self._server_sock = None

    def _cleanup_socket(self) -> None:
        if self.sock:
            with contextlib.suppress(OSError):
                self.sock.close()
            self.sock = None
        self._close_server_socket()

    def queue_get_nowait(self) -> dict[str, Any] | None:
        if self._pending:
            return self._pending.pop(0)
        try:
            return self.incoming.get_nowait()
        except queue.Empty:
            return None

    def queue_get(self, timeout: float | None = None) -> dict[str, Any] | None:
        try:
            return self.incoming.get(timeout=timeout)
        except queue.Empty:
            return None

    def queue_get_filtered(
        self,
        expected_types: set[str],
        timeout: float | None = None,
    ) -> dict[str, Any] | None:
        """Return the next packet matching one of *expected_types*.

        Packets that don't match are buffered in ``_pending`` so they
        aren't lost – they will be returned by a later call to
        ``queue_get_nowait`` or a subsequent ``queue_get_filtered``
        that accepts them.
        """
        deadline = time.monotonic() + timeout if timeout is not None else None

        # First drain any pending packets we already have.
        rest: list[dict[str, Any]] = []
        for p in self._pending:
            if p.get("type") in expected_types:
                self._pending = rest + self._pending[len(rest) + 1 :]
                return p
            rest.append(p)
        self._pending = rest

        while True:
            remaining: float | None = None
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None

            try:
                packet = self.incoming.get(
                    timeout=min(remaining, 0.25) if remaining else 0.25
                )
            except queue.Empty:
                continue

            if packet.get("type") in expected_types:
                return packet
            self._pending.append(packet)


def _recv_exact(sock: socket.socket, n: int) -> bytes | None:
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


def perform_handshake(
    conn: P2PConnection,
    timeout: float = HANDSHAKE_TIMEOUT_S,
) -> dict[str, Any] | None:
    """Start background, send handshake, wait for peer's handshake, validate version.

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


def _parse_type(packet: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    return packet.get("type", ""), packet.get("payload", {})
