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

        # Check for error status codes and provide detailed error message
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Try to extract detailed error message from response body
            try:
                error_detail = response.json()
                # Google APIs typically return errors in this format
                if "error" in error_detail:
                    error_info = error_detail["error"]
                    error_msg = f"TIM API Error ({response.status_code}): {error_info.get('message', str(error_info))}"
                else:
                    error_msg = f"TIM API Error ({response.status_code}): {error_detail}"
            except Exception:
                # If we can't parse the error as JSON, use the text
                error_msg = f"TIM API Error ({response.status_code}): {response.text}"

            # Raise a ValueError with the detailed message instead of HTTPStatusError
            raise ValueError(error_msg) from e

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
