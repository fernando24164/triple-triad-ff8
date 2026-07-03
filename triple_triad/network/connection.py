from __future__ import annotations

import contextlib
import logging
import queue
import socket
import threading
import time
from collections import deque
from typing import Any

from .framing import read_packet, send_packet
from .protocol import (
    HEARTBEAT_INTERVAL_S,
    HEARTBEAT_TIMEOUT_S,
    MessageType,
    make_disconnect,
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
        self._pending: deque[dict[str, Any]] = deque()
        self.is_host = False
        self.connected = False
        self.remote_name: str = ""
        self._send_lock = threading.Lock()

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
                    send_packet(self.sock, data)
                except (BrokenPipeError, OSError) as exc:
                    logger.warning("Send failed: %s", exc)
                    self.connected = False
                    self.incoming.put(make_packet(MessageType.CONNECTION_LOST))

    def close(self) -> None:
        if self.connected:
            with contextlib.suppress(Exception):
                self.send(make_disconnect())
        self.stop()

    def _receiver_loop(self) -> None:
        logger.debug("Receiver loop started (sock=%s)", self.sock is not None)
        while self._running and self.sock:
            try:
                packet = read_packet(self.sock)
                if packet is None:
                    if self._running:
                        logger.warning(
                            "Receiver: read_packet returned None — connection lost"
                        )
                        self.incoming.put(make_packet(MessageType.CONNECTION_LOST))
                    break
                msg_type, _ = parse_packet(packet)
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
            return self._pending.popleft()
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

        # First drain any pending packets we already have, preserving order
        # for the ones that don't match by rotating them to the back.
        for _ in range(len(self._pending)):
            p = self._pending.popleft()
            if p.get("type") in expected_types:
                return p
            self._pending.append(p)

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
