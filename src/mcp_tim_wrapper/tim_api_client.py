import httpx
from pydantic import ValidationError

from .models import (
    ComputeFlightEmissionsRequest,
    ComputeFlightEmissionsResponse,
    ComputeScope3FlightEmissionsRequest,
    ComputeScope3FlightEmissionsResponse,
    ComputeTypicalFlightEmissionsRequest,
    ComputeTypicalFlightEmissionsResponse,
)


class TravelImpactModelAPI:
    BASE_URL = "https://travelimpactmodel.googleapis.com/v1"

    def __init__(self, api_key: str, client: httpx.AsyncClient):
        if not api_key:
            raise ValueError("API key for Travel Impact Model API is required.")
        self.api_key = api_key
        self._client = client

    async def _make_request(self, endpoint: str, request_data: dict) -> httpx.Response:
        url = f"{self.BASE_URL}/{endpoint}?key={self.api_key}"
        response = await self._client.post(url, json=request_data)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response

    async def compute_flight_emissions(
        self, request: ComputeFlightEmissionsRequest
    ) -> ComputeFlightEmissionsResponse:
        response = await self._make_request(
            "flights:computeFlightEmissions", request.model_dump(by_alias=True)
        )
        try:
            return ComputeFlightEmissionsResponse.model_validate(response.json())
        except ValidationError as e:
            raise ValueError(f"Failed to parse response: {e}")

    async def compute_typical_flight_emissions(
        self, request: ComputeTypicalFlightEmissionsRequest
    ) -> ComputeTypicalFlightEmissionsResponse:
        response = await self._make_request(
            "flights:computeTypicalFlightEmissions", request.model_dump(by_alias=True)
        )
        try:
            return ComputeTypicalFlightEmissionsResponse.model_validate(response.json())
        except ValidationError as e:
            raise ValueError(f"Failed to parse response: {e}")

    async def compute_scope3_flight_emissions(
        self, request: ComputeScope3FlightEmissionsRequest
    ) -> ComputeScope3FlightEmissionsResponse:
        response = await self._make_request(
            "flights:computeScope3FlightEmissions", request.model_dump(by_alias=True)
        )
        try:
            return ComputeScope3FlightEmissionsResponse.model_validate(response.json())
        except ValidationError as e:
            raise ValueError(f"Failed to parse response: {e}")


# The get_tim_api_client function is removed as the client will be managed
# by the application's lifespan events.
