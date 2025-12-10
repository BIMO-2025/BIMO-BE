
import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock

# Mocking external dependencies
sys.modules["app.core.clients.amadeus"] = MagicMock()
sys.modules["app.feature.airlines.airline_service"] = MagicMock()
sys.modules["app.core.firebase"] = MagicMock()

from app.core.clients.amadeus import amadeus_client
from app.feature.airlines.airline_service import get_airline_statistics
from app.feature.flights.flights_schemas import FlightSearchRequest, AirlineSchema
from app.feature.flights.flights_service import search_flights

# Setup Mocks
async def mock_search_flights(*args, **kwargs):
    return [
        {
            "id": "1",
            "source": "GDS",
            "itineraries": [{"segments": [{"departure": {}, "arrival": {}}]}],
            "price": {"total": "500.00", "base": "400.00", "currency": "USD"},
            "validating_airline_codes": ["KE"]
        },
        {
            "id": "2",
            "source": "GDS",
            "itineraries": [{"segments": [{"departure": {}, "arrival": {}}]}],
            "price": {"total": "300.00", "base": "200.00", "currency": "USD"},
            "validating_airline_codes": ["OZ"]
        }
    ]

amadeus_client.search_flights = AsyncMock(side_effect=mock_search_flights)

async def mock_get_stats(code):
    if code == "KE":
        return AirlineSchema(
            airlineName="Korean Air",
            overallRating=4.5,
            totalReviews=100
        )
    elif code == "OZ":
        return AirlineSchema(
            airlineName="Asiana Airlines",
            overallRating=4.0,
            totalReviews=200
        )
    return None

# We need to monkeypath the function inside the module because it interprets the import at runtime
import app.feature.flights.flights_service as service_module
service_module.get_airline_statistics = mock_get_stats

async def test_search():
    print("Testing Search Logic...")
    
    # Test 1: Sort by Rating Desc
    req = FlightSearchRequest(
        origin="ICN", destination="JFK", departure_date="2025-01-01", 
        adults=1, sort_by="rating_desc"
    )
    res = await search_flights(req)
    
    print("\n[Result: Rating Desc]")
    for offer in res.flight_offers:
        print(f"Airline: {offer.airline_info.airlineName}, Rating: {offer.airline_info.overallRating}")
    
    assert res.flight_offers[0].airline_info.airlineName == "Korean Air" # 4.5 > 4.0
    
    # Test 2: Sort by Reviews Desc
    req.sort_by = "review_count_desc"
    res = await search_flights(req)
    print("\n[Result: Reviews Desc]")
    for offer in res.flight_offers:
        print(f"Airline: {offer.airline_info.airlineName}, Reviews: {offer.airline_info.totalReviews}")

    assert res.flight_offers[0].airline_info.airlineName == "Asiana Airlines" # 200 > 100
    
    print("\nSUCCESS: All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_search())
