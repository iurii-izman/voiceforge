"""Audio capture via PipeWire (pw-record)."""

import subprocess
import threading
from typing import BinaryIO

import numpy as np
import structlog

from voiceforge.audio.buffer import BYTES_PER_SAMPLE, CHANNELS, SAMPLE_RATE, RingBuffer

log = structlog.get_logger()

# Mic capture: raw s16le mono 16 kHz to stdout
PW_RECORD_CMD = [
    "pw-record",
    "--format=s16",
    "--rate=16000",
    "--channels=1",
    "-",  # stdout
]


def _pw_record_cmd(target_source: str | None = None) -> list[str]:
    """Build pw-record command; optional target_source for monitor (Block 6.3)."""
    cmd = list(PW_RECORD_CMD)
    if target_source:
        # Insert --target before "-" (stdout)
        cmd.insert(-1, f"--target={target_source}")
    return cmd


class AudioCapture:
    """Two streams: mic and system monitor via PipeWire."""

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        channels: int = CHANNELS,
        buffer_seconds: float = 60.0,
        monitor_source: str | None = None,
    ) -> None:
        self._sample_rate = sample_rate
        self._channels = channels
        self._buffer_seconds = buffer_seconds
        self._monitor_source = monitor_source
        self._mic_buffer: RingBuffer | None = None
        self._monitor_buffer: RingBuffer | None = None
        self._mic_proc: subprocess.Popen[bytes] | None = None
        self._monitor_proc: subprocess.Popen[bytes] | None = None
        self._mic_thread: threading.Thread | None = None
        self._monitor_thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        """Start pw-record for mic and (if available) monitor."""
        if self._mic_proc is not None:
            log.warning("capture.already_started")
            return
        self._stop.clear()
        self._mic_buffer = RingBuffer(self._buffer_seconds, self._sample_rate)
        self._monitor_buffer = RingBuffer(self._buffer_seconds, self._sample_rate)

        try:
            self._mic_proc = subprocess.Popen(  # nosec B603 B607 — pw-record is a trusted system binary
                PW_RECORD_CMD,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            log.error("capture.pw_record_not_found", hint="dnf install pipewire-utils")
            raise

        self._mic_thread = threading.Thread(
            target=self._reader_loop,
            args=(self._mic_proc, self._mic_proc.stdout, self._mic_buffer, "mic"),
            daemon=True,
        )
        self._mic_thread.start()

        # Monitor: pw-record from default or from loopback source (Block 6.3)
        monitor_cmd = _pw_record_cmd(self._monitor_source)
        try:
            self._monitor_proc = subprocess.Popen(  # nosec B603 B607 — pw-record monitor, trusted
                monitor_cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            self._monitor_thread = threading.Thread(
                target=self._reader_loop,
                args=(
                    self._monitor_proc,
                    self._monitor_proc.stdout,
                    self._monitor_buffer,
                    "monitor",
                ),
                daemon=True,
            )
            self._monitor_thread.start()
        except FileNotFoundError:
            self._monitor_proc = None
            self._monitor_thread = None
            log.warning("capture.monitor_not_started")

        log.info("capture.started", sample_rate=self._sample_rate)

    def _reader_loop(
        self,
        proc: subprocess.Popen[bytes] | None,
        stream: BinaryIO | None,
        buf: RingBuffer,
        name: str,
    ) -> None:
        if stream is None:
            return
        chunk_size = self._sample_rate * BYTES_PER_SAMPLE * self._channels  # ~1 sec
        while not self._stop.is_set():
            try:
                data = stream.read(chunk_size)
            except (ValueError, OSError):
                break
            if not data:
                rc = proc.poll() if proc is not None else None
                if rc is not None:
                    log.warning("capture.stream_closed", name=name, returncode=rc)
                break
            buf.write(data)
        log.debug("capture.reader_stopped", name=name)

    def stop(self) -> None:
        """Stop capture."""
        self._stop.set()
        for proc in (self._mic_proc, self._monitor_proc):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
        self._mic_proc = None
        self._monitor_proc = None
        if self._mic_thread is not None:
            self._mic_thread.join(timeout=2)
        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=2)
        self._mic_thread = None
        self._monitor_thread = None
        log.info("capture.stopped")

    def get_chunk(self, seconds: float) -> tuple[np.ndarray, np.ndarray]:
        """Return last N seconds: (mic, monitor) as int16 arrays."""
        mic = self._mic_buffer.read_last(seconds) if self._mic_buffer else np.array([], dtype=np.int16)
        mon = self._monitor_buffer.read_last(seconds) if self._monitor_buffer else np.array([], dtype=np.int16)
        return (mic, mon)

    def diagnostics(self) -> dict[str, object]:
        """Return runtime diagnostics useful for tests and troubleshooting."""
        mic_rc = self._mic_proc.poll() if self._mic_proc is not None else None
        mon_rc = self._monitor_proc.poll() if self._monitor_proc is not None else None
        mic_samples = 0
        mon_samples = 0
        if self._mic_buffer is not None:
            mic_samples = int(self._mic_buffer.read_last(1.0).size)
        if self._monitor_buffer is not None:
            mon_samples = int(self._monitor_buffer.read_last(1.0).size)
        return {
            "mic_returncode": mic_rc,
            "monitor_returncode": mon_rc,
            "mic_samples_last_1s": mic_samples,
            "monitor_samples_last_1s": mon_samples,
            "monitor_source": self._monitor_source,
        }
