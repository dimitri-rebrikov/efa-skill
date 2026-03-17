import asyncio
import argparse
import json
import math
import os
from typing import Any, Optional
from dateutil import parser as date_parser

from apyefa import EfaClient
from apyefa.data_classes import LocationFilter

DEFAULT_URL = "https://efa.de/efa"

class EfaCli:
    def __init__(self, url: Optional[str] = None):
        self.endpoint = url or os.getenv("EFA_URL", DEFAULT_URL)

    async def search_stations(self, name: str, limit: int = 5) -> list[dict]:
        async with EfaClient(self.endpoint) as client:
            locations = await client.locations_by_name(name, filters=[LocationFilter.STOPS], limit=limit)
            if not locations:
                raise ValueError(f"No stations found for '{name}'.")
            return [{"name": loc.name, "id": loc.id} for loc in locations]

    async def plan_trip(self, origin: str, destination: str, time: Optional[str] = None) -> dict:
        parsed_time = None
        if time:
            try:
                parsed_time = date_parser.parse(time)
            except Exception as e:
                raise ValueError(f"Invalid time format: {e}. Please use formats like '14:00' or '2024-12-25 14:00'.")

        async with EfaClient(self.endpoint) as client:
            origin_locs = await client.locations_by_name(origin, filters=[LocationFilter.STOPS], limit=1)
            dest_locs = await client.locations_by_name(destination, filters=[LocationFilter.STOPS], limit=1)
            if not origin_locs or not dest_locs:
                raise ValueError("Origin or destination not found.")
            origin = origin_locs[0]
            dest = dest_locs[0]

            try:
                journeys = await client.trip(origin, dest, trip_datetime=parsed_time)
                if not journeys:
                    raise ValueError("No trips found.")
                data = []
                for journey in journeys[:3]:
                    legs_data = []
                    for leg in journey.legs:
                        line = leg.transport.name or leg.transport.number or 'Line'
                        duration_min = math.ceil(leg.duration / 60)
                        try:
                            planned = leg.raw_data['origin']['departureTimePlanned']
                            start_str = date_parser.parse(planned).strftime("%H:%M")
                            estimated = leg.raw_data['origin'].get('departureTimeEstimated')
                            est_str = None
                            if estimated and estimated != planned:
                                est_str = date_parser.parse(estimated).strftime('%H:%M')
                        except (KeyError, ValueError):
                            start_str = "N/A"
                            est_str = None
                        legs_data.append({
                            "start": start_str,
                            "estimated": est_str,
                            "line": line,
                            "origin": leg.origin.name,
                            "destination": leg.destination.name,
                            "duration_minutes": duration_min
                        })
                    data.append({"interchanges": journey.interchanges, "legs": legs_data})
                return {"journeys": data}
            except Exception as e:
                raise ValueError(f"Trip planning failed: {e}")

    async def get_departures(self, location: str, limit: int = 10, time: Optional[str] = None) -> dict:
        parsed_time = None
        if time:
            try:
                parsed_time = date_parser.parse(time)
            except Exception as e:
                raise ValueError(f"Invalid time format: {e}. Please use formats like '14:00' or '2024-12-25 14:00'.")
        async with EfaClient(self.endpoint) as client:
            locs = await client.locations_by_name(location, filters=[LocationFilter.STOPS], limit=1)
            if not locs:
                raise ValueError(f"No location found for '{location}'.")
            loc = locs[0]
            departures = await client.departures_by_location(loc, limit=limit, arg_date=parsed_time)
            if not departures:
                raise ValueError(f"No departures from {loc.name}.")
            data = []
            for dep in departures:
                time_str = dep.planned_time.strftime("%H:%M")
                est_str = None
                if dep.estimated_time and dep.estimated_time != dep.planned_time:
                    est_str = dep.estimated_time.strftime("%H:%M")
                data.append({
                    "start": time_str,
                    "estimated": est_str,
                    "line": dep.line_name,
                    "destination": dep.destination.name
                })
            return {"location_name": loc.name, "departures": data}


def format_search_stations(data: list[dict]) -> str:
    result = "Stations:\n"
    for loc in data:
        result += f"- {loc['name']}"
        if loc.get('id'):
            result += f" (ID: {loc['id']})"
        result += "\n"
    return result


def format_trip(data: dict) -> str:
    result = "Trips:\n"
    for journey in data["journeys"]:
        result += f"Changes: {journey['interchanges']}\n"
        for leg in journey["legs"]:
            start_str = leg['start']
            if leg.get('estimated'):
                start_str += f" (est. {leg['estimated']})"
            result += f"  ({start_str}) {leg['line']}: {leg['origin']} -> {leg['destination']} ({leg['duration_minutes']} min)\n"
    return result


def format_departures(data: dict) -> str:
    result = f"Upcoming departures from {data['location_name']}:\n"
    for dep in data["departures"]:
        time_str = dep['start']
        if dep.get('estimated'):
            time_str += f" (est. {dep['estimated']})"
        result += f"- {time_str} {dep['line']} -> {dep['destination']}\n"
    return result


async def main():
    formatters = {
        'search-stations': format_search_stations,
        'trip': format_trip,
        'departures': format_departures
    }
    parser = argparse.ArgumentParser(description="EFA CLI for VVS")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Search stations
    search_parser = subparsers.add_parser('search-stations', help='Search stations')
    search_parser.add_argument('name', help='Station name or ID')
    search_parser.add_argument('--limit', type=int, default=5, help='Limit results')
    search_parser.add_argument('--json', action='store_true', help='Output JSON instead of human-readable format')

    # Trip
    trip_parser = subparsers.add_parser('trip', help='Plan trip')
    trip_parser.add_argument('origin', help='Origin name or ID')
    trip_parser.add_argument('destination', help='Destination name or ID')
    trip_parser.add_argument('--time', help='Departure time (optional)')
    trip_parser.add_argument('--json', action='store_true', help='Output JSON instead of human-readable format')

    # Departures
    dep_parser = subparsers.add_parser('departures', help='Get departures')
    dep_parser.add_argument('location', help='Location name or ID')
    dep_parser.add_argument('--limit', type=int, default=10, help='Limit results')
    dep_parser.add_argument('--time', help='Time (e.g. "20:20", "Dienstag 20:20")')
    dep_parser.add_argument('--json', action='store_true', help='Output JSON instead of human-readable format')

    args = parser.parse_args()

    cli = EfaCli()

    if args.command:
        try:
            if args.command == 'search-stations':
                data = await cli.search_stations(args.name, args.limit)
            elif args.command == 'trip':
                data = await cli.plan_trip(args.origin, args.destination, args.time)
            elif args.command == 'departures':
                data = await cli.get_departures(args.location, args.limit, args.time)
            else:
                parser.print_help()
                return

            if args.json:
                print(json.dumps(data, indent=2))
            else:
                print(formatters[args.command](data))
        except ValueError as e:
            error_msg = str(e)
            if args.json:
                print(json.dumps({"error": error_msg}, indent=2))
            else:
                print(error_msg)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())