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


async def test_get_scope3_flight_emissions_without_dated(mock_context, mock_api_client):
    # Arrange - Test that scope3 works when modelVersion.dated is None (real API behavior)
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
        modelVersion=ModelVersion(major=2, minor=0, patch=0),  # No dated field
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
    assert result["modelVersion"]["dated"] is None
    mock_api_client.compute_scope3_flight_emissions.assert_awaited_once()


# Batch endpoint tests


async def test_get_typical_flight_emissions_batch_success(
    mock_context, mock_api_client
):
    # Arrange
    from mcp_tim_wrapper.main import get_typical_flight_emissions_batch

    mock_response = ComputeTypicalFlightEmissionsResponse(
        typicalFlightEmissions=[
            TypicalFlightEmission(
                market=Market(origin="LAX", destination="JFK"),
                emissionsGramsPerPax=EmissionsGramsPerPax(economy=100, business=200),
            ),
            TypicalFlightEmission(
                market=Market(origin="SFO", destination="LHR"),
                emissionsGramsPerPax=EmissionsGramsPerPax(economy=450, business=900),
            ),
        ],
        modelVersion=ModelVersion(major=1, minor=0, patch=0, dated="2023-01-01"),
    )
    mock_api_client.compute_typical_flight_emissions.return_value = mock_response

    # Act
    markets = [
        Market(origin="LAX", destination="JFK"),
        Market(origin="SFO", destination="LHR"),
    ]
    result = await get_typical_flight_emissions_batch(mock_context, markets)

    # Assert
    assert result == mock_response.model_dump(by_alias=True)
    assert len(result["typicalFlightEmissions"]) == 2
    mock_api_client.compute_typical_flight_emissions.assert_awaited_once()


async def test_get_typical_flight_emissions_batch_error(mock_context, mock_api_client):
    # Arrange
    from mcp_tim_wrapper.main import get_typical_flight_emissions_batch

    mock_api_client.compute_typical_flight_emissions.side_effect = ValueError(
        "Invalid market in batch"
    )

    # Act & Assert
    markets = [Market(origin="XXX", destination="YYY")]
    with pytest.raises(ToolError, match="Invalid market in batch"):
        await get_typical_flight_emissions_batch(mock_context, markets)


async def test_get_specific_flight_emissions_batch_success(
    mock_context, mock_api_client
):
    # Arrange
    from mcp_tim_wrapper.main import get_specific_flight_emissions_batch

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
            ),
            FlightWithEmissions(
                flight=Flight(
                    origin="JFK",
                    destination="LAX",
                    operatingCarrierCode="AA",
                    flightNumber=100,
                    departureDate=Date(year=2024, month=10, day=2),
                ),
                emissionsGramsPerPax=EmissionsGramsPerPax(economy=150, business=300),
            ),
        ],
        modelVersion=ModelVersion(major=1, minor=0, patch=0, dated="2023-01-01"),
    )
    mock_api_client.compute_flight_emissions.return_value = mock_response

    # Act
    flights = [
        Flight(
            origin="SFO",
            destination="LHR",
            operatingCarrierCode="UA",
            flightNumber=901,
            departureDate=Date(year=2024, month=10, day=1),
        ),
        Flight(
            origin="JFK",
            destination="LAX",
            operatingCarrierCode="AA",
            flightNumber=100,
            departureDate=Date(year=2024, month=10, day=2),
        ),
    ]
    result = await get_specific_flight_emissions_batch(mock_context, flights)

    # Assert
    assert result == mock_response.model_dump(by_alias=True)
    assert len(result["flightEmissions"]) == 2
    mock_api_client.compute_flight_emissions.assert_awaited_once()


async def test_get_specific_flight_emissions_batch_error(mock_context, mock_api_client):
    # Arrange
    from mcp_tim_wrapper.main import get_specific_flight_emissions_batch

    mock_api_client.compute_flight_emissions.side_effect = ValueError(
        "Flight not found"
    )

    # Act & Assert
    flights = [
        Flight(
            origin="SFO",
            destination="LHR",
            operatingCarrierCode="XX",
            flightNumber=999,
            departureDate=Date(year=2024, month=10, day=1),
        ),
    ]
    with pytest.raises(ToolError, match="Flight not found"):
        await get_specific_flight_emissions_batch(mock_context, flights)


async def test_get_scope3_flight_emissions_batch_success(mock_context, mock_api_client):
    # Arrange
    from mcp_tim_wrapper.main import get_scope3_flight_emissions_batch

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
            ),
            Scope3FlightWithEmissions(
                flight=Scope3Flight(
                    departureDate=Date(year=2024, month=11, day=15),
                    cabinClass="BUSINESS",
                    distanceKm="5000",
                ),
                wtwEmissionsGramsPerPax="25000",
                source="TIM_EMISSIONS",
                ttwEmissionsGramsPerPax="20000",
                wttEmissionsGramsPerPax="5000",
            ),
        ],
        modelVersion=ModelVersion(major=1, minor=0, patch=0, dated="2023-01-01"),
    )
    mock_api_client.compute_scope3_flight_emissions.return_value = mock_response

    # Act
    flights = [
        Scope3Flight(
            departureDate=Date(year=2024, month=10, day=1),
            cabinClass="ECONOMY",
            origin="JFK",
            destination="SFO",
        ),
        Scope3Flight(
            departureDate=Date(year=2024, month=11, day=15),
            cabinClass="BUSINESS",
            distanceKm="5000",
        ),
    ]
    result = await get_scope3_flight_emissions_batch(mock_context, flights)

    # Assert
    assert result == mock_response.model_dump(by_alias=True)
    assert len(result["flightEmissions"]) == 2
    mock_api_client.compute_scope3_flight_emissions.assert_awaited_once()


async def test_get_scope3_flight_emissions_batch_error(mock_context, mock_api_client):
    # Arrange
    from mcp_tim_wrapper.main import get_scope3_flight_emissions_batch

    mock_api_client.compute_scope3_flight_emissions.side_effect = ValueError(
        "Invalid cabin class"
    )

    # Act & Assert
    flights = [
        Scope3Flight(
            departureDate=Date(year=2024, month=10, day=1),
            cabinClass="INVALID",
            origin="JFK",
            destination="SFO",
        ),
    ]
    with pytest.raises(ToolError, match="Invalid cabin class"):
        await get_scope3_flight_emissions_batch(mock_context, flights)
