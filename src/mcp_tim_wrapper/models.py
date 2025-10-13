from typing import List, Optional
from pydantic import BaseModel, Field


# Common Models
class Date(BaseModel):
    year: int
    month: int
    day: int


class EmissionsGramsPerPax(BaseModel):
    first: Optional[int] = None
    business: Optional[int] = None
    premium_economy: Optional[int] = Field(None, alias="premiumEconomy")
    economy: Optional[int] = None


class ModelVersion(BaseModel):
    major: int
    minor: int
    patch: int
    dated: Optional[str] = None


# Models for computeFlightEmissions
class Flight(BaseModel):
    origin: str
    destination: str
    operating_carrier_code: str = Field(alias="operatingCarrierCode")
    flight_number: int = Field(alias="flightNumber")
    departure_date: Date = Field(alias="departureDate")


class ComputeFlightEmissionsRequest(BaseModel):
    flights: List[Flight]


class FlightWithEmissions(BaseModel):
    flight: Flight
    emissions_grams_per_pax: Optional[EmissionsGramsPerPax] = Field(
        None, alias="emissionsGramsPerPax"
    )


class ComputeFlightEmissionsResponse(BaseModel):
    flight_emissions: List[FlightWithEmissions] = Field(alias="flightEmissions")
    model_version: ModelVersion = Field(alias="modelVersion")


# Models for computeTypicalFlightEmissions
class Market(BaseModel):
    origin: str
    destination: str


class ComputeTypicalFlightEmissionsRequest(BaseModel):
    markets: List[Market]


class TypicalFlightEmission(BaseModel):
    market: Market
    emissions_grams_per_pax: EmissionsGramsPerPax = Field(alias="emissionsGramsPerPax")


class ComputeTypicalFlightEmissionsResponse(BaseModel):
    typical_flight_emissions: List[TypicalFlightEmission] = Field(
        alias="typicalFlightEmissions"
    )
    model_version: ModelVersion = Field(alias="modelVersion")


# Models for computeScope3FlightEmissions
class Scope3Flight(BaseModel):
    departure_date: Date = Field(alias="departureDate")
    cabin_class: str = Field(alias="cabinClass")
    origin: Optional[str] = None
    destination: Optional[str] = None
    carrier_code: Optional[str] = Field(None, alias="carrierCode")
    flight_number: Optional[int] = Field(None, alias="flightNumber")
    distance_km: Optional[str] = Field(None, alias="distanceKm")


class ComputeScope3FlightEmissionsRequest(BaseModel):
    flights: List[Scope3Flight]
    model_version: Optional[ModelVersion] = Field(None, alias="modelVersion")


class Scope3FlightWithEmissions(BaseModel):
    flight: Scope3Flight
    wtw_emissions_grams_per_pax: str = Field(alias="wtwEmissionsGramsPerPax")
    source: str
    ttw_emissions_grams_per_pax: str = Field(alias="ttwEmissionsGramsPerPax")
    wtt_emissions_grams_per_pax: str = Field(alias="wttEmissionsGramsPerPax")


class ComputeScope3FlightEmissionsResponse(BaseModel):
    flight_emissions: List[Scope3FlightWithEmissions] = Field(alias="flightEmissions")
    model_version: ModelVersion = Field(alias="modelVersion")
