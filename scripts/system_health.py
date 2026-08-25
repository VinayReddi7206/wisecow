#!/usr/bin/env python3
"""
System Health Monitoring Script  (Problem Statement 2, objective #1)

Monitors CPU, memory, disk usage and the running-process count on a Linux
system. If any metric crosses its threshold, an ALERT is written to the
console AND appended to a log file (system_health.log).

Usage:
    pip install psutil
    python3 system_health.py                 # single check
    python3 system_health.py --watch 5       # re-check every 5 seconds

Thresholds (override with flags):
    --cpu 80   --mem 80   --disk 80   --procs 300
"""
import argparse
import datetime
import logging
import sys

try:
    import psutil
except ImportError:
    print("This script needs 'psutil'. Install it with:  pip install psutil")
    sys.exit(1)

LOG_FILE = "system_health.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def report(line: str, level: str = "info") -> None:
    """Print to console and write to the log file."""
    print(line)
    getattr(logging, level)(line)


def check(cpu_t, mem_t, disk_t, proc_t) -> bool:
    """Run one health check. Returns True if everything is healthy."""
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report(f"----- Health check @ {stamp} -----")

    healthy = True

    # CPU (sampled over 1 second for an accurate reading)
    cpu = psutil.cpu_percent(interval=1)
    if cpu > cpu_t:
        report(f"ALERT: CPU usage high: {cpu:.1f}% (threshold {cpu_t}%)", "warning")
        healthy = False
    else:
        report(f"OK   : CPU usage {cpu:.1f}%")

    # Memory
    mem = psutil.virtual_memory().percent
    if mem > mem_t:
        report(f"ALERT: Memory usage high: {mem:.1f}% (threshold {mem_t}%)", "warning")
        healthy = False
    else:
        report(f"OK   : Memory usage {mem:.1f}%")

    # Disk (root filesystem)
    disk = psutil.disk_usage("/").percent
    if disk > disk_t:
        report(f"ALERT: Disk usage high: {disk:.1f}% (threshold {disk_t}%)", "warning")
        healthy = False
    else:
        report(f"OK   : Disk usage {disk:.1f}%")

    # Running processes
    procs = len(psutil.pids())
    if procs > proc_t:
        report(f"ALERT: Too many processes: {procs} (threshold {proc_t})", "warning")
        healthy = False
    else:
        report(f"OK   : Running processes {procs}")

    if healthy:
        report("RESULT: system healthy.\n")
    else:
        report("RESULT: one or more metrics EXCEEDED thresholds!\n", "warning")
    return healthy


def main() -> None:
    p = argparse.ArgumentParser(description="Linux system health monitor")
    p.add_argument("--cpu", type=float, default=80, help="CPU %% threshold")
    p.add_argument("--mem", type=float, default=80, help="Memory %% threshold")
    p.add_argument("--disk", type=float, default=80, help="Disk %% threshold")
    p.add_argument("--procs", type=int, default=300, help="Process-count threshold")
    p.add_argument("--watch", type=int, metavar="SECONDS",
                   help="Repeat the check every N seconds (Ctrl+C to stop)")
    a = p.parse_args()

    if a.watch:
        import time
        report(f"Starting continuous monitoring every {a.watch}s. Ctrl+C to stop.")
        try:
            while True:
                check(a.cpu, a.mem, a.disk, a.procs)
                time.sleep(a.watch)
        except KeyboardInterrupt:
            report("Monitoring stopped by user.")
    else:
        healthy = check(a.cpu, a.mem, a.disk, a.procs)
        sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    main()
