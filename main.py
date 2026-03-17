import asyncio
import argparse
import math
import os
from typing import Optional
from dateutil import parser as date_parser

from apyefa import EfaClient
from apyefa.data_classes import LocationFilter

DEFAULT_URL = "https://efa.de/efa"

class EfaCli:
    def __init__(self, url: Optional[str] = None):
        self.endpoint = url or os.getenv("EFA_URL", DEFAULT_URL)

    async def search_stations(self, name: str, limit: int = 5) -> str:
        async with EfaClient(self.endpoint) as client:
            locations = await client.locations_by_name(name, filters=[LocationFilter.STOPS], limit=limit)
            if not locations:
                return f"No stations found for '{name}'."
            result = f"Stations:\n"
            for loc in locations:
                result += f"- {loc.name}"
                if loc.id:
                    result += f" (ID: {loc.id})"
                result += "\n"
            return result

    async def plan_trip(self, origin: str, destination: str, time: Optional[str] = None) -> str:
        parsed_time = None
        if time:
            try:
                parsed_time = date_parser.parse(time)
            except Exception as e:
                return f"Invalid time format: {e}. Please use formats like '14:00' or '2024-12-25 14:00'."

        async with EfaClient(self.endpoint) as client:
            origin_locs = await client.locations_by_name(origin, filters=[LocationFilter.STOPS], limit=1)
            dest_locs = await client.locations_by_name(destination, filters=[LocationFilter.STOPS], limit=1)
            if not origin_locs or not dest_locs:
                return "Origin or destination not found."
            origin = origin_locs[0]
            dest = dest_locs[0]

            try:
                journeys = await client.trip(origin, dest, trip_datetime=parsed_time)
                if not journeys:
                    return "No trips found."
                result = "Trips:\n"
                for journey in journeys[:3]:
                    result += f"Changes: {journey.interchanges}\n"
                    for leg in journey.legs:
                        line = leg.transport.name or leg.transport.number or 'Line'
                        duration_min = math.ceil(leg.duration / 60)
                        try:
                            planned = leg.raw_data['origin']['departureTimePlanned']
                            start_str = date_parser.parse(planned).strftime("%H:%M")
                            estimated = leg.raw_data['origin'].get('departureTimeEstimated')
                            if estimated and estimated != planned:
                                start_str += f" (est. {date_parser.parse(estimated).strftime('%H:%M')})"
                        except (KeyError, ValueError):
                            start_str = "N/A"
                        result += f"  ({start_str}) {line}: {leg.origin.name} -> {leg.destination.name} ({duration_min} min)\n"
                return result
            except Exception as e:
                return f"Trip planning failed: {e}"

    async def get_departures(self, location: str, limit: int = 10, time: Optional[str] = None) -> str:
        parsed_time = date_parser.parse(time) if time else None
        async with EfaClient(self.endpoint) as client:
            locs = await client.locations_by_name(location, filters=[LocationFilter.STOPS], limit=1)
            if not locs:
                return f"No location found for '{location}'."
            loc = locs[0]
            departures = await client.departures_by_location(loc, limit=limit, arg_date=parsed_time)
            if not departures:
                return f"No departures from {loc.name}."
            result = f"Upcoming departures from {loc.name}:\n"
            for dep in departures:
                time_str = dep.planned_time.strftime("%H:%M")
                if dep.estimated_time and dep.estimated_time != dep.planned_time:
                    time_str += f" (est. {dep.estimated_time.strftime('%H:%M')})"
                result += f"- {time_str} {dep.line_name} -> {dep.destination.name}\n"
            return result



async def main():
    parser = argparse.ArgumentParser(description="EFA CLI for VVS")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Search stations
    search_parser = subparsers.add_parser('search-stations', help='Search stations')
    search_parser.add_argument('name', help='Station name or ID')
    search_parser.add_argument('--limit', type=int, default=5, help='Limit results')

    # Trip
    trip_parser = subparsers.add_parser('trip', help='Plan trip')
    trip_parser.add_argument('origin', help='Origin name or ID')
    trip_parser.add_argument('destination', help='Destination name or ID')
    trip_parser.add_argument('--time', help='Departure time (optional)')

    # Departures
    dep_parser = subparsers.add_parser('departures', help='Get departures')
    dep_parser.add_argument('location', help='Location name or ID')
    dep_parser.add_argument('--limit', type=int, default=10, help='Limit results')
    dep_parser.add_argument('--time', help='Time (e.g. "20:20", "Dienstag 20:20")')

    args = parser.parse_args()

    cli = EfaCli()

    if args.command == 'search-stations':
        print(await cli.search_stations(args.name, args.limit))
    elif args.command == 'trip':
        print(await cli.plan_trip(args.origin, args.destination, args.time))
    elif args.command == 'departures':
        print(await cli.get_departures(args.location, args.limit, args.time))
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())