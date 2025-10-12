import pytest
from unittest.mock import MagicMock, AsyncMock
from mcp.server.fastmcp.exceptions import ToolError
from mcp_tim_wrapper.main import app
from mcp_tim_wrapper.models import (
    ComputeFlightEmissionsResponse,
    ComputeTypicalFlightEmissionsResponse,
    ComputeScope3FlightEmissionsResponse,
    FlightWithEmissions,
    TypicalFlightEmission,
    Scope3FlightWithEmissions,
    ModelVersion,
    Flight,
    Market,
    Scope3Flight,
    Date,
    EmissionsGramsPerPax,
)
from fastapi.testclient import TestClient
from mcp.server.fastmcp import Context

pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_api_client():
    # Use AsyncMock for async methods
    return AsyncMock()


@pytest.fixture
def mock_context(mock_api_client):
    # Create a mock that mimics the nested structure: context.request_context.request.app.state.api_client
    mock_context = MagicMock(spec=Context)
    mock_context.request_context.request.app.state.api_client = mock_api_client
    return mock_context


@pytest.fixture
def client(mock_api_client):
    app.state.api_client = mock_api_client
    with TestClient(app) as c:
        yield c


async def test_get_typical_flight_emissions_success(mock_context, mock_api_client):
    # Arrange
    from mcp_tim_wrapper.main import get_typical_flight_emissions

    mock_response = ComputeTypicalFlightEmissionsResponse(
        typicalFlightEmissions=[
            TypicalFlightEmission(
                market=Market(origin="LAX", destination="JFK"),
                emissionsGramsPerPax=EmissionsGramsPerPax(economy=100, business=200),
            )
        ],
        modelVersion=ModelVersion(major=1, minor=0, patch=0, dated="2023-01-01"),
    )
    mock_api_client.compute_typical_flight_emissions.return_value = mock_response

    # Act
    result = await get_typical_flight_emissions(mock_context, "LAX", "JFK")

    # Assert
    assert result == mock_response.model_dump(by_alias=True)
    mock_api_client.compute_typical_flight_emissions.assert_awaited_once()


async def test_get_typical_flight_emissions_error(mock_context, mock_api_client):
    # Arrange
    from mcp_tim_wrapper.main import get_typical_flight_emissions

    mock_api_client.compute_typical_flight_emissions.side_effect = ValueError(
        "Invalid market"
    )

    # Act & Assert
    with pytest.raises(ToolError, match="Invalid market"):
        await get_typical_flight_emissions(mock_context, "LAX", "JFK")


async def test_get_specific_flight_emissions_success(mock_context, mock_api_client):
    # Arrange
    from mcp_tim_wrapper.main import get_specific_flight_emissions

    mock_response = ComputeFlightEmissionsResponse(
        flightEmissions=[
            FlightWithEmissions(
                flight=Flight(
                    origin="SFO",
                    destination="LHR",
                    operatingCarrierCode="UA",
                    flightNumber=901,
                    departureDate=Date(year=2024, month=10, day=1),
                ),
                emissionsGramsPerPax=EmissionsGramsPerPax(economy=500, first=1500),
            )
        ],
        modelVersion=ModelVersion(major=1, minor=0, patch=0, dated="2023-01-01"),
    )
    mock_api_client.compute_flight_emissions.return_value = mock_response

    # Act
    result = await get_specific_flight_emissions(
        mock_context,
        origin="SFO",
        destination="LHR",
        operating_carrier_code="UA",
        flight_number=901,
        departure_year=2024,
        departure_month=10,
        departure_day=1,
    )

    # Assert
    assert result == mock_response.model_dump(by_alias=True)
    mock_api_client.compute_flight_emissions.assert_awaited_once()


async def test_get_scope3_flight_emissions_success(mock_context, mock_api_client):
    # Arrange
    from mcp_tim_wrapper.main import get_scope3_flight_emissions

    mock_response = ComputeScope3FlightEmissionsResponse(
        flightEmissions=[
            Scope3FlightWithEmissions(
                flight=Scope3Flight(
                    departureDate=Date(year=2024, month=10, day=1),
                    cabinClass="ECONOMY",
                    origin="JFK",
                    destination="SFO",
                ),
                wtwEmissionsGramsPerPax="12345",
                source="TIM_EMISSIONS",
                ttwEmissionsGramsPerPax="10000",
                wttEmissionsGramsPerPax="2345",
            )
        ],
        modelVersion=ModelVersion(major=1, minor=0, patch=0, dated="2023-01-01"),
    )
    mock_api_client.compute_scope3_flight_emissions.return_value = mock_response

    # Act
    result = await get_scope3_flight_emissions(
        mock_context,
        departure_year=2024,
        departure_month=10,
        departure_day=1,
        cabin_class="ECONOMY",
        origin="JFK",
        destination="SFO",
    )

    # Assert
    assert result == mock_response.model_dump(by_alias=True)
    mock_api_client.compute_scope3_flight_emissions.assert_awaited_once()
