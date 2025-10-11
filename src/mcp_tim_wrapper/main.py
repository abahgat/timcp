from contextlib import asynccontextmanager
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.exceptions import ToolError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
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

# Define a lifespan context manager to manage the httpx client
@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.environ.get("TRAVEL_IMPACT_MODEL_API_KEY")
    if not api_key:
        raise ValueError("TRAVEL_IMPACT_MODEL_API_KEY environment variable not set.")

    async with httpx.AsyncClient() as client:
        # Store the client in the app's state
        app.state.api_client = TravelImpactModelAPI(api_key=api_key, client=client)
        yield

# Create the main FastAPI application
app = FastAPI(lifespan=lifespan)

# Create the FastMCP application
mcp_app = FastMCP(
    name="Google Travel Impact Model Wrapper",
    instructions="A wrapper for the Google Travel Impact Model API, providing tools to calculate flight emissions.",
)

# Add a health check endpoint to the mcp application
@mcp_app.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health_check(request: Request) -> Response:
    return JSONResponse({"status": "ok"})


@mcp_app.tool(
    name="get_typical_flight_emissions",
    title="Get Typical Flight Emissions",
    description="Retrieves typical flight emissions estimates between two airports (a market).",
)
async def get_typical_flight_emissions(context: Context, origin: str, destination: str) -> dict:
    try:
        client: TravelImpactModelAPI = context.request_context.request.app.state.api_client
        api_request = ComputeTypicalFlightEmissionsRequest(
            markets=[Market(origin=origin, destination=destination)]
        )
        response = await client.compute_typical_flight_emissions(api_request)
        return response.model_dump(by_alias=True)
    except (ValueError, httpx.HTTPStatusError) as e:
        raise ToolError(str(e))


@mcp_app.tool(
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
        client: TravelImpactModelAPI = context.request_context.request.app.state.api_client
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


@mcp_app.tool(
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
        client: TravelImpactModelAPI = context.request_context.request.app.state.api_client
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


# Get the Starlette app from FastMCP and mount it
# This must be done after all routes and tools are defined.
app.mount("/", mcp_app.streamable_http_app())
