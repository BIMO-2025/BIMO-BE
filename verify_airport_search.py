import sys
import asyncio
from unittest.mock import MagicMock

# 1. Mock dependencies
sys.modules["amadeus"] = MagicMock()
mock_amadeus = MagicMock()
sys.modules["amadeus"].Client = MagicMock(return_value=mock_amadeus)

# Mock fastapi.concurrency
async def mock_run(func, *args, **kwargs):
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return func(*args, **kwargs)

mock_concurrency = MagicMock()
mock_concurrency.run_in_threadpool = mock_run
sys.modules["fastapi.concurrency"] = mock_concurrency

# 2. Import service after mocking
from app.feature.flights import flights_service
from app.core.clients.amadeus import amadeus_client

# 3. Setup Mock Data
mock_locations_response = {
    "data": [
        {
            "id": "ICN",
            "name": "INCHEON INTL",
            "detailedName": "SEOUL/KR:INCHEON INTL",
            "iataCode": "ICN",
            "subType": "AIRPORT",
            "geoCode": {"latitude": 37.469, "longitude": 126.450},
            "address": {"cityCode": "SEL", "countryCode": "KR"}
        },
        {
            "id": "SEL",
            "name": "SEOUL",
            "detailedName": "SEOUL/KR",
            "iataCode": "SEL",
            "subType": "CITY",
            "geoCode": {"latitude": 37.56, "longitude": 126.98},
            "address": {"cityCode": "SEL", "countryCode": "KR"}
        }
    ]
}

# Mock the client call
# amadeus_client.client.reference_data.locations.get -> returns mock response
amadeus_client.client = MagicMock()
amadeus_client.client.reference_data.locations.get.return_value = mock_locations_response

# 4. Run Test
async def run_test():
    print("Running Airport Search Verification...")
    keyword = "Seoul"
    
    print(f"Searching for: {keyword}")
    response = await flights_service.search_locations(keyword)
    
    print(f"\nFound {response.count} locations:")
    print("-" * 60)
    print(f"{'Type':<10} | {'IATA':<5} | {'Name'}")
    print("-" * 60)
    
    for loc in response.locations:
        print(f"{loc.sub_type:<10} | {loc.iata_code:<5} | {loc.name}")
        
        # Validation
        if not loc.iata_code:
            print("❌ Error: Missing IATA Code")
            
    # Check if both Airport and City are found
    types = [loc.sub_type for loc in response.locations]
    if "AIRPORT" in types and "CITY" in types:
        print("\n[PASS] Successfully retrieved both AIRPORT and CITY data.")
    else:
        print("\n[FAIL] Did not retrieve expected location types.")

if __name__ == "__main__":
    asyncio.run(run_test())
