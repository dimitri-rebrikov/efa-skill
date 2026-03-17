#!/bin/bash

echo "🚇 EFA CLI Demo"
echo "=================================================="

# Enable command tracing to show commands as they execute
set -x

uv run python main.py search-stations "Stuttgart Hauptbahnhof" --limit 3

uv run python main.py search-stations "Berlin" --limit 5

uv run python main.py trip "Stuttgart Hauptbahnhof" "Stuttgart Airport"

uv run python main.py trip "Stuttgart Hauptbahnhof" "Stuttgart Schwabstraße" --time "14:00"

uv run python main.py departures "Stuttgart Hauptbahnhof" --limit 5

EFA_URL="https://www3.vvs.de/mngvvs/" uv run python main.py departures "Stuttgart Schwabstraße" --limit 4 --time "15:30"

uv run python main.py --help

echo "JSON output examples:"
uv run python main.py search-stations "Stuttgart Hbf" --limit 3 --json
uv run python main.py trip "Stuttgart Hbf" "Stuttgart Airport" --json
uv run python main.py departures "Stuttgart Hbf" --limit 3 --json

# Disable command tracing
set +x

echo "=================================================="
echo "Demo completed! 🎉"
