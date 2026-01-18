from contextlib import asynccontextmanager
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.exceptions import ToolError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.middleware.cors import CORSMiddleware
import httpx
import os

from .models import (
    Date,
    Flight,
    ComputeFlightEmissionsRequest,
    Market,
    ComputeTypicalFlightEmissionsRequest,
    Scope3Flight,
    ComputeScope3FlightEmissionsRequest,
)
from .tim_api_client import TravelImpactModelAPI
from typing import List

# Create the FastMCP application
mcp = FastMCP(
    name="Google Travel Impact Model Wrapper",
    instructions="A wrapper for the Google Travel Impact Model API, providing tools to calculate flight emissions.",
)


# Add a health check endpoint to the mcp application
@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health_check(request: Request) -> Response:
    return JSONResponse({"status": "ok"})


@mcp.tool(
    name="tim_get_typical_flight_emissions",
    title="Get Typical Flight Emissions",
    description="""Retrieves typical flight emissions estimates between two airports (a market).

Required parameters:
- origin: IATA airport code (e.g., "JFK", "LAX")
- destination: IATA airport code (e.g., "LHR", "SFO")

Example: get_typical_flight_emissions(origin="JFK", destination="LAX")

Returns emissions estimates in grams per passenger for different cabin classes.

Note: This endpoint provides average emissions and does not require a date.""",
)
async def get_typical_flight_emissions(
    context: Context, origin: str, destination: str
) -> dict:
    try:
        client: TravelImpactModelAPI = (
            context.request_context.request.app.state.api_client
        )
        api_request = ComputeTypicalFlightEmissionsRequest(
            markets=[Market(origin=origin, destination=destination)]
        )
        response = await client.compute_typical_flight_emissions(api_request)
        return response.model_dump(by_alias=True)
    except ValueError as e:
        raise ToolError(str(e))


@mcp.tool(
    name="tim_get_specific_flight_emissions",
    title="Get Specific Flight Emissions",
    description="""Retrieves emission estimates for a specific flight on a given date.

Required parameters:
- origin: IATA airport code (e.g., "JFK")
- destination: IATA airport code (e.g., "LAX")
- operating_carrier_code: IATA airline code (e.g., "UA" for United, "AA" for American)
- flight_number: Flight number as integer (e.g., 123)
- departure_year: Year (e.g., 2024)
- departure_month: Month 1-12 (e.g., 10 for October)
- departure_day: Day 1-31 (e.g., 15)

Example: get_specific_flight_emissions(
    origin="JFK",
    destination="LAX",
    operating_carrier_code="UA",
    flight_number=123,
    departure_year=2024,
    departure_month=10,
    departure_day=15
)

Returns emissions estimates in grams per passenger for different cabin classes.

IMPORTANT: Departure date must be in the future. This endpoint uses real flight schedule data.""",
)
async def get_specific_flight_emissions(
    context: Context,
    origin: str,
    destination: str,
    operating_carrier_code: str,
    flight_number: int,
    departure_year: int,
    departure_month: int,
    departure_day: int,
) -> dict:
    try:
        client: TravelImpactModelAPI = (
            context.request_context.request.app.state.api_client
        )
        api_request = ComputeFlightEmissionsRequest(
            flights=[
                Flight(
                    origin=origin,
                    destination=destination,
                    operatingCarrierCode=operating_carrier_code,
                    flightNumber=flight_number,
                    departureDate=Date(
                        year=departure_year, month=departure_month, day=departure_day
                    ),
                )
            ]
        )
        response = await client.compute_flight_emissions(api_request)
        return response.model_dump(by_alias=True)
    except ValueError as e:
        raise ToolError(str(e))


@mcp.tool(
    name="tim_get_scope3_flight_emissions",
    title="Get Scope 3 Flight Emissions",
    description="""Retrieves GHG emissions estimates for flight segments for Scope 3 reporting.

This endpoint accepts historical dates and is designed for reporting past travel.

Required parameters:
- departure_year: Year (e.g., 2024)
- departure_month: Month 1-12 (e.g., 10)
- departure_day: Day 1-31 (e.g., 15)
- cabin_class: One of "ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", or "FIRST"

IMPORTANT - Distance specification (choose ONE):
You MUST provide EITHER:
  Option A: Both origin AND destination (IATA codes like "JFK", "LAX")
  Option B: distance_km (as a string, e.g., "5000")

Optional parameters (for more specific queries):
- carrier_code: IATA airline code (e.g., "UA")
- flight_number: Flight number as integer (e.g., 123)

Examples:
1. Using origin/destination:
   get_scope3_flight_emissions(
       departure_year=2024,
       departure_month=10,
       departure_day=15,
       cabin_class="ECONOMY",
       origin="JFK",
       destination="LAX"
   )

2. Using distance_km:
   get_scope3_flight_emissions(
       departure_year=2024,
       departure_month=10,
       departure_day=15,
       cabin_class="BUSINESS",
       distance_km="5000"
   )

Returns Well-to-Wake (WTW), Tank-to-Wake (TTW), and Well-to-Tank (WTT) emissions in grams per passenger.

NOTE: This tool processes one flight at a time. For calculating emissions for multiple flights,
use get_scope3_flight_emissions_batch which is more efficient.""",
)
async def get_scope3_flight_emissions(
    context: Context,
    departure_year: int,
    departure_month: int,
    departure_day: int,
    cabin_class: str,
    origin: str | None = None,
    destination: str | None = None,
    carrier_code: str | None = None,
    flight_number: int | None = None,
    distance_km: str | None = None,
) -> dict:
    try:
        client: TravelImpactModelAPI = (
            context.request_context.request.app.state.api_client
        )
        api_request = ComputeScope3FlightEmissionsRequest(
            flights=[
                Scope3Flight(
                    departureDate=Date(
                        year=departure_year, month=departure_month, day=departure_day
                    ),
                    cabinClass=cabin_class,
                    origin=origin,
                    destination=destination,
                    carrierCode=carrier_code,
                    flightNumber=flight_number,
                    distanceKm=distance_km,
                )
            ]
        )
        response = await client.compute_scope3_flight_emissions(api_request)
        return response.model_dump(by_alias=True)
    except ValueError as e:
        raise ToolError(str(e))


# Batch endpoints for efficient multi-flight processing
@mcp.tool(
    name="tim_get_typical_flight_emissions_batch",
    title="Get Typical Flight Emissions (Batch)",
    description="""Retrieves typical flight emissions for multiple airport pairs (markets) in a single request.

This is more efficient than calling get_typical_flight_emissions multiple times.

Required parameter:
- markets: List of market objects, each with:
  - origin: IATA airport code (e.g., "JFK")
  - destination: IATA airport code (e.g., "LAX")

Example:
markets = [
    {"origin": "JFK", "destination": "LAX"},
    {"origin": "SFO", "destination": "LHR"}
]

Returns emissions estimates for all markets in grams per passenger for different cabin classes.

Note: This endpoint provides average emissions and does not require dates.""",
)
async def get_typical_flight_emissions_batch(
    context: Context, markets: List[Market]
) -> dict:
    try:
        client: TravelImpactModelAPI = (
            context.request_context.request.app.state.api_client
        )
        api_request = ComputeTypicalFlightEmissionsRequest(markets=markets)
        response = await client.compute_typical_flight_emissions(api_request)
        return response.model_dump(by_alias=True)
    except ValueError as e:
        raise ToolError(str(e))


@mcp.tool(
    name="tim_get_specific_flight_emissions_batch",
    title="Get Specific Flight Emissions (Batch)",
    description="""Retrieves emission estimates for multiple specific flights in a single request.

This is more efficient than calling get_specific_flight_emissions multiple times.

Required parameter:
- flights: List of flight objects, each with:
  - origin: IATA airport code (e.g., "JFK")
  - destination: IATA airport code (e.g., "LAX")
  - operatingCarrierCode: IATA airline code (e.g., "UA")
  - flightNumber: Flight number as integer (e.g., 123)
  - departureDate: Object with year, month, day (e.g., {"year": 2024, "month": 10, "day": 15})

Example:
flights = [
    {
        "origin": "JFK",
        "destination": "LAX",
        "operatingCarrierCode": "UA",
        "flightNumber": 123,
        "departureDate": {"year": 2024, "month": 10, "day": 15}
    },
    {
        "origin": "SFO",
        "destination": "LHR",
        "operatingCarrierCode": "BA",
        "flightNumber": 456,
        "departureDate": {"year": 2024, "month": 11, "day": 20}
    }
]

Returns emissions estimates for all flights in grams per passenger for different cabin classes.

IMPORTANT: All departure dates must be in the future. This endpoint uses real flight schedule data.""",
)
async def get_specific_flight_emissions_batch(
    context: Context, flights: List[Flight]
) -> dict:
    try:
        client: TravelImpactModelAPI = (
            context.request_context.request.app.state.api_client
        )
        api_request = ComputeFlightEmissionsRequest(flights=flights)
        response = await client.compute_flight_emissions(api_request)
        return response.model_dump(by_alias=True)
    except ValueError as e:
        raise ToolError(str(e))


@mcp.tool(
    name="tim_get_scope3_flight_emissions_batch",
    title="Get Scope 3 Flight Emissions (Batch)",
    description="""Retrieves GHG emissions for multiple flight segments in a single request for Scope 3 reporting.

This is more efficient than calling get_scope3_flight_emissions multiple times.

This endpoint accepts historical dates and is designed for reporting past travel.

Required parameter:
- flights: List of flight objects, each with:
  - departureDate: Object with year, month, day (e.g., {"year": 2024, "month": 10, "day": 15})
  - cabinClass: One of "ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", or "FIRST"
  - EITHER origin AND destination (IATA codes) OR distanceKm (as string)
  - Optional: carrierCode (IATA airline code) and flightNumber (integer)

Example:
flights = [
    {
        "departureDate": {"year": 2024, "month": 10, "day": 15},
        "cabinClass": "ECONOMY",
        "origin": "JFK",
        "destination": "LAX"
    },
    {
        "departureDate": {"year": 2024, "month": 11, "day": 20},
        "cabinClass": "BUSINESS",
        "distanceKm": "5000"
    }
]

Returns Well-to-Wake (WTW), Tank-to-Wake (TTW), and Well-to-Tank (WTT) emissions in grams per passenger for all flights.""",
)
async def get_scope3_flight_emissions_batch(
    context: Context, flights: List[Scope3Flight]
) -> dict:
    try:
        client: TravelImpactModelAPI = (
            context.request_context.request.app.state.api_client
        )
        api_request = ComputeScope3FlightEmissionsRequest(flights=flights)
        response = await client.compute_scope3_flight_emissions(api_request)
        return response.model_dump(by_alias=True)
    except ValueError as e:
        raise ToolError(str(e))


# Get the Starlette app from FastMCP
# This must be done after all routes and tools are defined.
mcp_app = mcp.streamable_http_app()

# Add CORS middleware to support browser-based MCP clients like MCP Inspector
# WARNING: This configuration allows requests from any localhost origin.
# For production, replace with specific allowed origins (e.g., ["https://yourdomain.com"])
allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:*,http://127.0.0.1:*"
).split(",")

mcp_app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_origin_regex=(
        r"http://(localhost|127\.0\.0\.1):\d+"
        if "localhost:*" in str(allowed_origins)
        else None
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id", "mcp-protocol-version"],
    max_age=86400,
)


# Define a combined lifespan context manager
@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    api_key = os.environ.get("TRAVEL_IMPACT_MODEL_API_KEY")
    if not api_key:
        raise ValueError("TRAVEL_IMPACT_MODEL_API_KEY environment variable not set.")

    # Start both the httpx client and MCP app's lifespan
    async with httpx.AsyncClient() as client:
        # IMPORTANT: Store API client in BOTH app states.
        # When mcp_app is mounted, tools access context.request_context.request.app.state,
        # which refers to the mounted app (mcp_app), not the parent app.
        # Without storing in both, tools fail with: 'State' object has no attribute 'api_client'
        api_client = TravelImpactModelAPI(api_key=api_key, client=client)
        app.state.api_client = api_client
        mcp_app.state.api_client = api_client

        # Initialize MCP's task group via its lifespan
        async with mcp_app.router.lifespan_context(mcp_app):
            yield


# Create the main FastAPI application with combined lifespan
app = FastAPI(lifespan=combined_lifespan)

# Mount the MCP app
app.mount("/", mcp_app)
