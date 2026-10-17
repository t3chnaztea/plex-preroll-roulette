#!/usr/bin/env python3
"""Plex pre-roll roulette.

Every run (e.g. cron, every 30 min) rolls a weighted die: with probability
PREROLL_ODDS it sets the Plex "Movie pre-roll video" pref to a random bumper
from the pool; otherwise it clears the pref so movies start with no pre-roll.
Net effect: a movie started at a random moment has ~ODDS chance of getting a
surprise pre-roll (FBI warning / feature-presentation / drive-in / countdown).

Requires Plex Pass (pre-roll is a Pass feature).

Configuration (all via environment variables):

  PLEX_URL        Plex base URL. Default: http://localhost:32400
  PLEX_TOKEN      Plex auth token. If unset, the script tries to read it live
                  from a Docker container's Preferences.xml (see below), so no
                  secret has to be stored. How to find your token:
                  https://support.plex.tv/articles/204059436

  Pool of clips (one of these is required). The paths written to Plex must be
  what the Plex SERVER sees (inside the container, if Plex runs in Docker):
  PREROLL_DIR     A directory to scan for video files (non-recursive). Scanned
                  on the host this script runs on.
  PREROLL_PLEX_DIR  Optional. The same folder as the Plex server sees it, when
                  that differs from PREROLL_DIR (e.g. the script runs on the
                  Docker host and the folder is mapped into the container at
                  another path). Clip paths are written under this directory.
                  Default: PREROLL_DIR.
  PREROLL_FILES   Comma-separated explicit list of clip paths, as the Plex
                  server sees them. Takes precedence over PREROLL_DIR if both
                  are set.

  Clips whose path contains "," or ";" are skipped with a warning: Plex reads
  those characters as list separators in the pre-roll pref and has no escape.

  PREROLL_ODDS    Chance (0..1) a pre-roll is active after a run. Default: 0.10
  PREROLL_LOG     Log file path. Default: stderr only.

  Docker token fallback (only used when PLEX_TOKEN is unset):
  PLEX_CONTAINER  Container name. Default: plex
  PLEX_PREFS      Preferences.xml path inside the container.
                  Default: /config/Library/Application Support/Plex Media Server/Preferences.xml

Example:
  PLEX_TOKEN=xxxx PREROLL_DIR=/media/PreRolls ./plex-preroll-roulette.py
"""
import os
import random
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime

PLEX_URL = os.environ.get("PLEX_URL", "http://localhost:32400").rstrip("/")
ODDS = float(os.environ.get("PREROLL_ODDS", "0.10"))
LOG = os.environ.get("PREROLL_LOG", "")

VIDEO_EXTS = (".mp4", ".mkv", ".mov", ".m4v", ".avi", ".webm")


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {msg}"
    print(line, file=sys.stderr)
    if LOG:
        with open(LOG, "a") as f:
            f.write(line + "\n")


def get_token():
    token = os.environ.get("PLEX_TOKEN")
    if token:
        return token
    # Fallback: read the live token from a Docker container's Preferences.xml.
    container = os.environ.get("PLEX_CONTAINER", "plex")
    prefs = os.environ.get(
        "PLEX_PREFS",
        "/config/Library/Application Support/Plex Media Server/Preferences.xml",
    )
    out = subprocess.check_output(
        ["docker", "exec", container, "grep", "-o",
         'PlexOnlineToken="[^"]*"', prefs],
        text=True,
    )
    return out.split('"')[1]


def build_pool():
    files = os.environ.get("PREROLL_FILES")
    if files:
        return _usable([p.strip() for p in files.split(",") if p.strip()])
    directory = os.environ.get("PREROLL_DIR")
    if directory:
        plex_dir = os.environ.get("PREROLL_PLEX_DIR") or directory
        try:
            names = sorted(os.listdir(directory))
        except OSError as e:
            log(f"ERROR reading PREROLL_DIR {directory}: {e}")
            return []
        return _usable([
            os.path.join(plex_dir, n)
            for n in names
            if n.lower().endswith(VIDEO_EXTS)
        ])
    return []


def _usable(paths):
    # Plex splits the pre-roll pref on "," (sequential) and ";" (random), with
    # no escape, so a path containing either would be read as several paths.
    ok = []
    for p in paths:
        if "," in p or ";" in p:
            log(f"WARN skipping {p}: Plex treats ',' and ';' as separators")
        else:
            ok.append(p)
    return ok


def set_preroll(token, value):
    qs = urllib.parse.urlencode(
        {"CinemaTrailersPrerollID": value, "X-Plex-Token": token}
    )
    req = urllib.request.Request(f"{PLEX_URL}/:/prefs?{qs}", method="PUT")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status


def main():
    try:
        token = get_token()
    except Exception as e:  # noqa: BLE001
        log(f"ERROR getting token: {e}")
        sys.exit(1)

    # Build and validate the pool on every run, not just winning rolls, so a
    # bad config fails loudly right away instead of ~ODDS of the time.
    pool = build_pool()
    if not pool:
        log("ERROR no pre-roll clips found (set PREROLL_DIR or PREROLL_FILES)")
        sys.exit(1)

    if random.random() < ODDS:
        choice = random.choice(pool)
        action = choice
    else:
        choice = ""
        action = "(cleared)"

    try:
        code = set_preroll(token, choice)
        log(f"set -> {action} [{code}]")
    except Exception as e:  # noqa: BLE001
        log(f"ERROR setting preroll: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
