# plex-preroll-roulette

Surprise your Plex movie nights. Every run rolls a weighted die: with some
probability it sets Plex's **Movie pre-roll video** to a random bumper from your
pool, otherwise it clears it. Run it on a timer and a movie started at a random
moment has roughly that chance of opening with a surprise intro: an FBI
anti-piracy warning, a "Our Feature Presentation" bumper, a drive-in
intermission, an SMPTE countdown leader, whatever you put in the pool.

Requires **Plex Pass** (pre-roll is a Pass feature).

## How it works

Plex exposes a single "pre-roll" preference (`CinemaTrailersPrerollID`). This
script doesn't pick per-playback: instead, on each run it either points that
pref at one random clip or blanks it. With the default 10% odds and a 30-minute
cron, any given movie launch has about a 1-in-10 chance of a pre-roll being
armed. Low odds keep it a rare delight rather than a chore.

## Setup

1. Drop your bumper clips into a folder the **Plex server** can see. If Plex
   runs in Docker, that's the path *inside* the container (e.g. a `PreRolls`
   folder mapped into `/media`).
2. Get a Plex token: https://support.plex.tv/articles/204059436 (or use the
   Docker fallback below).
3. Schedule the script (cron example below).

## Configuration

All via environment variables:

| Variable        | Default                     | Notes |
|-----------------|-----------------------------|-------|
| `PLEX_URL`      | `http://localhost:32400`    | Plex base URL. |
| `PLEX_TOKEN`    | _(unset)_                   | Plex auth token. If unset, falls back to reading it live from a Docker container (see below). |
| `PREROLL_DIR`   | _(unset)_                   | Folder to scan for video clips (non-recursive). Paths are what the **Plex server** sees. |
| `PREROLL_FILES` | _(unset)_                   | Comma-separated explicit clip list. Takes precedence over `PREROLL_DIR`. |
| `PREROLL_ODDS`  | `0.10`                      | Chance (0..1) a pre-roll is armed after a run. |
| `PREROLL_LOG`   | _(unset)_                   | Optional log file; always logs to stderr too. |

Docker token fallback (only used when `PLEX_TOKEN` is unset):

| Variable         | Default | Notes |
|------------------|---------|-------|
| `PLEX_CONTAINER` | `plex`  | Container name. The script runs `docker exec` to grep the token out of `Preferences.xml`, so no secret is stored on disk. |
| `PLEX_PREFS`     | `/config/Library/Application Support/Plex Media Server/Preferences.xml` | Preferences path inside the container. |

## Usage

```sh
# Explicit token + a folder of clips
PLEX_TOKEN=xxxxxxxx PREROLL_DIR=/media/PreRolls ./plex-preroll-roulette.py

# Docker host: let it read the token from the running container
PLEX_CONTAINER=plex PREROLL_DIR=/media/PreRolls ./plex-preroll-roulette.py

# Explicit clip list, 25% odds, with a log file
PREROLL_FILES="/media/PreRolls/fbi.mp4,/media/PreRolls/countdown.mp4" \
  PREROLL_ODDS=0.25 PREROLL_LOG=/var/log/plex-preroll.log \
  PLEX_TOKEN=xxxxxxxx ./plex-preroll-roulette.py
```

### Cron

```cron
# Roll every 30 minutes
*/30 * * * * PLEX_TOKEN=xxxxxxxx PREROLL_DIR=/media/PreRolls /usr/local/bin/plex-preroll-roulette.py >/dev/null 2>&1
```

No external dependencies: standard-library Python 3 only.

## More tiny tools for home labs

Agent skills: [unifi](https://github.com/t3chnaztea/unifi-skills) · [home-assistant](https://github.com/t3chnaztea/home-assistant-skills) · [batocera](https://github.com/t3chnaztea/batocera-skills) · [psn](https://github.com/t3chnaztea/awesome-psn-skills) · [arr-stack](https://github.com/t3chnaztea/arr-stack-skills)  
Retro cabinet: [batocera-toolbox](https://github.com/t3chnaztea/batocera-toolbox) · [batocera-holidays](https://github.com/t3chnaztea/batocera-holidays)  
Home server: [dell-ipmi-fan-control](https://github.com/t3chnaztea/dell-ipmi-fan-control)  
PlayStation: [awesome-psnstats](https://github.com/t3chnaztea/awesome-psnstats)  
Desktop: [fastfetch-macos-gradient-hud](https://github.com/t3chnaztea/fastfetch-macos-gradient-hud)

## License

MIT. See [LICENSE](LICENSE).
