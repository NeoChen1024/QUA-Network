# SPDX-License-Identifier: Apache-2.0
"""Log the APRS-IS full feed to hourly plain-text files.

Connects to an APRS-IS server (full feed on port 10152 by default), logs in
receive-only (passcode -1), and appends every packet line as raw bytes to a
file rotated hourly (UTC). Each stored line is:

    <unix_time>\\t<raw TNC2 line>\\n

Raw bytes are kept untouched so byte-length statistics and later re-analysis
stay faithful to what the server sent. No compression is applied; rely on
the filesystem's transparent compression instead.

While running, every packet is echoed to stdout and periodic statistics are
printed to stderr.
"""

import os
import signal
import socket
import sys
import time

import click

SERVER_COMMENT = b"#"


def _raise_interrupt(signum, frame):
    raise KeyboardInterrupt


def fmt_time(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts))


def log(msg):
    print(f"[{fmt_time(time.time())}] {msg}", file=sys.stderr, flush=True)


def log_path(out_dir, ts):
    name = time.strftime("aprsis-%Y%m%d-%H", time.gmtime(ts)) + ".log"
    return os.path.join(out_dir, name)


def open_log(path):
    fh = open(path, "ab")
    # A previous run killed mid-write may have left a partial last line;
    # terminate it so our first record starts on a fresh line.
    if fh.tell() > 0:
        with open(path, "rb") as r:
            r.seek(-1, os.SEEK_END)
            if r.read(1) != b"\n":
                fh.write(b"\n")
    return fh


class Stats:
    """Counters spanning the whole program run (across reconnects)."""

    def __init__(self):
        self.start = time.time()
        self.packets = 0
        self.bytes = 0
        self.connects = 0
        self.iv_start = self.start
        self.iv_packets = 0
        self.iv_bytes = 0

    def add(self, nbytes):
        self.packets += 1
        self.bytes += nbytes
        self.iv_packets += 1
        self.iv_bytes += nbytes

    def report(self, now):
        up = max(now - self.start, 1e-9)
        iv = max(now - self.iv_start, 1e-9)
        h, rem = divmod(int(up), 3600)
        m, s = divmod(rem, 60)
        log(
            f"stats: uptime {h}:{m:02d}:{s:02d}, connects {self.connects} | "
            f"last {iv:.0f}s: {self.iv_packets} pkts, "
            f"{self.iv_packets / iv * 60:.1f} pkt/min, {self.iv_bytes / iv / 1024:.1f} KiB/s | "
            f"total: {self.packets} pkts, avg {self.packets / up * 60:.1f} pkt/min, "
            f"{self.bytes / 1048576:.2f} MiB"
        )
        self.iv_start = now
        self.iv_packets = 0
        self.iv_bytes = 0


def stream(call, server, port, out, stats_interval, quiet, stats):
    login = f"user {call} pass -1 vers aprsis-logger 0.2\r\n".encode()
    fh = None
    try:
        log(f"connecting to {server}:{port} ...")
        with socket.create_connection((server, port), timeout=120) as sock:
            stats.connects += 1
            log(f"connected to {sock.getpeername()[0]}:{port}, logging in as {call}")
            sock.sendall(login)
            buf = b""
            cur_path = None
            last_report = time.time()
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    raise ConnectionError("server closed connection")
                buf += chunk
                now = time.time()
                path = log_path(out, now)
                if path != cur_path:
                    if fh:
                        fh.close()
                    fh = open_log(path)
                    cur_path = path
                    log(f"writing to {path}")
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.rstrip(b"\r")
                    if not line:
                        continue
                    if line.startswith(SERVER_COMMENT):
                        log(f"server: {line.decode('utf-8', 'replace')}")
                        continue
                    fh.write(f"{now:.3f}\t".encode() + line + b"\n")
                    stats.add(len(line))
                    if not quiet:
                        print(line.decode("utf-8", "replace"), flush=False)
                if not quiet:
                    sys.stdout.flush()
                if now - last_report >= stats_interval:
                    fh.flush()
                    stats.report(now)
                    last_report = now
    finally:
        # Runs on network errors, KeyboardInterrupt and SIGTERM alike.
        if fh:
            fh.close()


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--call", required=True, help="Your callsign, used for the APRS-IS login.")
@click.option("--server", default="rotate.aprs.net", show_default=True, help="APRS-IS server.")
@click.option("--port", type=int, default=10152, show_default=True, help="Server port; 10152 is the full feed.")
@click.option("--out", type=click.Path(file_okay=False), default="./corpus", show_default=True, help="Output directory.")
@click.option("--stats-interval", type=float, default=60, show_default=True, help="Seconds between statistics reports.")
@click.option("-q", "--quiet", is_flag=True, help="Do not echo packets to stdout; statistics are still printed.")
def cli(call, server, port, out, stats_interval, quiet):
    # SIGTERM (systemd stop, docker stop) would otherwise skip the finally block.
    signal.signal(signal.SIGTERM, _raise_interrupt)
    os.makedirs(out, exist_ok=True)
    stats = Stats()
    backoff = 5
    try:
        while True:
            started = time.time()
            try:
                stream(call, server, port, out, stats_interval, quiet, stats)
            except (OSError, ConnectionError) as e:
                if time.time() - started > 300:
                    backoff = 5  # the connection was healthy for a while; reset
                log(f"connection error: {e}; retry in {backoff}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 300)
    except KeyboardInterrupt:
        log("interrupted, exiting")
        stats.report(time.time())


if __name__ == "__main__":
    cli()
