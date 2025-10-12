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
    name="get_typical_flight_emissions",
    title="Get Typical Flight Emissions",
    description="Retrieves typical flight emissions estimates between two airports (a market).",
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
    except (ValueError, httpx.HTTPStatusError) as e:
        raise ToolError(str(e))


@mcp.tool(
    name="get_specific_flight_emissions",
    title="Get Specific Flight Emissions",
    description="Retrieves emission estimates for a specific flight.",
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
    except (ValueError, httpx.HTTPStatusError) as e:
        raise ToolError(str(e))


@mcp.tool(
    name="get_scope3_flight_emissions",
    title="Get Scope 3 Flight Emissions",
    description="Retrieves GHG emissions estimates for a set of flight segments for Scope 3 reporting.",
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
    except (ValueError, httpx.HTTPStatusError) as e:
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
        # Store the client in the app's state
        app.state.api_client = TravelImpactModelAPI(api_key=api_key, client=client)

        # Initialize MCP's task group via its lifespan
        async with mcp_app.router.lifespan_context(mcp_app):
            yield


# Create the main FastAPI application with combined lifespan
app = FastAPI(lifespan=combined_lifespan)

# Mount the MCP app
app.mount("/", mcp_app)
