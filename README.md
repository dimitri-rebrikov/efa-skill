# EFA CLI for OpenClaw

OpenClaw skill for public transit queries using [apyefa](https://github.com/alex-jung/apyefa) (version 1.1.8+) with support for trip planning time parameters.

## Features

- `search_stations(name, limit=5)`: Find stations by name/ID.
- `plan_trip(origin, dest, time=None)`: Trip routes with optional departure time.
- `get_departures(location, limit=10, time=None)`: Departures with flexible time queries.

All commands support `--json` flag for JSON output instead of human-readable format.

Location: name or ID "de:08111:6118"

Time: "20:20", "25 Apr 20:20", "Dienstag 20:20" (dateutil fuzzy parsing).

Default URL for EFA requests: https://efa.de/efa

Configurable via `EFA_URL` environment variable.

## Setup

```bash
uv sync
```

## Demo / CLI

Run the demo script to see all commands in action:

```bash
bash demo.sh
```

Or try individual commands:

```bash
uv run python main.py search-stations "Stuttgart Hbf" --limit 3
uv run python main.py trip "Stuttgart Hbf" "Stuttgart Flughafen"
uv run python main.py trip "Stuttgart Hbf" "Stuttgart Airport" --time "14:00"
uv run python main.py departures "de:08111:6118" --time "Dienstag 20:20"
```

For JSON output, add the `--json` flag:

```bash
uv run python main.py search-stations "Stuttgart Hbf" --limit 3 --json
uv run python main.py trip "Stuttgart Hbf" "Stuttgart Airport" --json
uv run python main.py departures "de:08111:6118" --json
```

## OpenClaw Usage

Add to skills directory.

on Test: `openclaw agent --message "use efa cli for trip from Hbf to airport"`

Class: `EfaCli` (OpenClaw)

CLI ready.

## Dependencies

Managed by uv:
- `apyefa>=1.1.8` (official release with bug fixes)
- `python-dateutil` for flexible time parsing
- `aiohttp` (transitive dependency)

## Note

This project uses apyefa version 1.1.8 or later, which includes fixes for trip planning with time parameters. The schema validation bug that previously prevented using the `trip_datetime` parameter has been resolved in the official release.
