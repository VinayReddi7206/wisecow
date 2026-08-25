#!/usr/bin/env python3
"""
Application Health Checker  (Problem Statement 2, objective #4)

Checks whether an application is 'UP' or 'DOWN' by inspecting the HTTP
status code it returns. Uses only the Python standard library (no installs).

- UP   : the app responds with a 2xx or 3xx status code.
- DOWN : the app responds with 4xx/5xx, times out, or cannot be reached.

Usage:
    python3 app_health_checker.py https://wisecow.local --insecure
    python3 app_health_checker.py http://localhost:4499
    python3 app_health_checker.py https://example.com --watch 10
"""
import argparse
import datetime
import logging
import ssl
import sys
import urllib.request
import urllib.error

LOG_FILE = "app_health.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def log(line: str, level: str = "info") -> None:
    print(line)
    getattr(logging, level)(line)


def check_once(url: str, timeout: int, insecure: bool) -> bool:
    """Return True if the app is UP, False if DOWN."""
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # For self-signed TLS (our Wisecow HTTPS), allow skipping verification.
    ctx = None
    if insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "health-checker"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            code = resp.getcode()
            if 200 <= code < 400:
                log(f"[{stamp}] UP   - {url} responded {code}")
                return True
            log(f"[{stamp}] DOWN - {url} responded {code}", "warning")
            return False
    except urllib.error.HTTPError as e:
        # Server answered, but with an error status (4xx/5xx).
        log(f"[{stamp}] DOWN - {url} returned HTTP {e.code}", "warning")
        return False
    except urllib.error.URLError as e:
        log(f"[{stamp}] DOWN - {url} unreachable ({e.reason})", "error")
        return False
    except Exception as e:  # timeouts and anything unexpected
        log(f"[{stamp}] DOWN - {url} error ({e})", "error")
        return False


def main() -> None:
    p = argparse.ArgumentParser(description="Application uptime / health checker")
    p.add_argument("url", help="Application URL to check (http/https)")
    p.add_argument("--timeout", type=int, default=5, help="Request timeout (seconds)")
    p.add_argument("--insecure", action="store_true",
                   help="Skip TLS verification (use for self-signed certs)")
    p.add_argument("--watch", type=int, metavar="SECONDS",
                   help="Re-check every N seconds (Ctrl+C to stop)")
    a = p.parse_args()

    if a.watch:
        import time
        log(f"Monitoring {a.url} every {a.watch}s. Ctrl+C to stop.")
        try:
            while True:
                check_once(a.url, a.timeout, a.insecure)
                time.sleep(a.watch)
        except KeyboardInterrupt:
            log("Monitoring stopped by user.")
    else:
        up = check_once(a.url, a.timeout, a.insecure)
        sys.exit(0 if up else 1)


if __name__ == "__main__":
    main()
