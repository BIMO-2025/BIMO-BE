from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class FlightStatus(str, Enum):
    SCHEDULED = "scheduled"
    BOARDING = "boarding"
    FLYING = "flying"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class FlightSeatClass(str, Enum):
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"

class AirportInfo(BaseModel):
    code: str
    name: str
    city: str
    time: str # ISO format datetime

class FlightAirlineInfo(BaseModel):
    name: str
    code: str
    logo_url: Optional[str] = None

class MyFlightCreate(BaseModel):
    airline_id: str
    flight_number: str
    departure_code: str
    arrival_code: str
    departure_time: str
    seat_class: FlightSeatClass = FlightSeatClass.ECONOMY
    
class MyFlight(BaseModel):
    id: str
    user_id: str
    flight_number: str
    airline: FlightAirlineInfo
    departure: AirportInfo
    arrival: AirportInfo
    seat_class: FlightSeatClass
    status: FlightStatus
    created_at: str

class FlightStats(BaseModel):
    total_flight_time_minutes: int
    total_distance_km: int
    visited_countries_count: int
