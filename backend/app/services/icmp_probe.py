from __future__ import annotations

import os
import socket
import struct
import threading
import time


class ICMPUnavailableError(Exception):
    """Raised when raw ICMP sockets are not available."""


class ICMPProbe:
    """Minimal ICMP echo (ping) probe using a raw socket.

    Requires raw-socket privileges; raises ``ICMPUnavailableError`` when
    the OS denies it so callers can fall back to TCP probing. One socket
    is created lazily per thread and reused across probes.
    """

    def __init__(self, timeout: float = 1.0) -> None:
        self.timeout = timeout
        self._local = threading.local()

    def probe(self, address: str) -> bool | None:
        """Return ``True`` on an echo reply, ``False`` on timeout.

        Returns ``None`` when raw ICMP sockets are unavailable.
        """
        try:
            sock = self._socket()
        except ICMPUnavailableError:
            return None

        ident = self._local.ident
        self._local.seq = (self._local.seq + 1) & 0xFFFF
        seq = self._local.seq

        payload = struct.pack("!d", time.monotonic())
        header = struct.pack("!BBHHH", 8, 0, 0, ident, seq)
        packet = struct.pack(
            "!BBHHH", 8, 0, self._checksum(header + payload), ident, seq
        ) + payload

        try:
            sock.sendto(packet, (address, 1))
        except OSError:
            return False

        deadline = time.monotonic() + self.timeout

        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()

            if remaining <= 0:
                break

            try:
                sock.settimeout(remaining)
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                return False
            except OSError:
                return False

            if addr[0] == address and self._is_echo_reply(data, ident, seq):
                return True

        return False

    def _socket(self) -> socket.socket:
        sock = getattr(self._local, "sock", None)

        if sock is None:
            try:
                sock = socket.socket(
                    socket.AF_INET,
                    socket.SOCK_RAW,
                    socket.IPPROTO_ICMP,
                )
            except (PermissionError, OSError) as exc:
                raise ICMPUnavailableError(str(exc)) from exc

            sock.settimeout(self.timeout)
            self._local.sock = sock
            self._local.ident = (os.getpid() ^ threading.get_ident()) & 0xFFFF
            self._local.seq = 0

        return sock

    @staticmethod
    def _checksum(data: bytes) -> int:
        if len(data) % 2:
            data += b"\x00"

        total = sum(struct.unpack(f"!{len(data) // 2}H", data))
        total = (total >> 16) + (total & 0xFFFF)
        total += total >> 16

        return (~total) & 0xFFFF

    @staticmethod
    def _is_echo_reply(data: bytes, ident: int, seq: int) -> bool:
        offset = 0

        if data and (data[0] >> 4) == 4:
            offset = (data[0] & 0x0F) * 4

        if len(data) < offset + 8:
            return False

        icmp_type, _code, _checksum, reply_id, reply_seq = struct.unpack(
            "!BBHHH",
            data[offset : offset + 8],
        )

        return icmp_type == 0 and reply_id == ident and reply_seq == seq