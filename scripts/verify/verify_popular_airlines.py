import sys
import asyncio
from unittest.mock import MagicMock

# 1. Mock dependencies BEFORE import
mock_firebase = MagicMock()
mock_db = MagicMock()
mock_firebase.db = mock_db
sys.modules["app.core.firebase"] = mock_firebase

# Mock fastapi.concurrency.run_in_threadpool
# We will just run the function directly
async def mock_run_in_threadpool(func, *args, **kwargs):
    return func(*args, **kwargs)

mock_fastapi_concurrency = MagicMock()
mock_fastapi_concurrency.run_in_threadpool = mock_run_in_threadpool
sys.modules["fastapi.concurrency"] = mock_fastapi_concurrency

# 2. Import service
# Note: airline_service imports 'db' from app.core.firebase
from app.feature.airlines import airline_service
from app.feature.airlines.models import Airline

# 3. Setup Mock Data
def create_mock_doc(airline_id, review_count, rating):
    mock_doc = MagicMock()
    mock_doc.id = airline_id
    mock_doc.to_dict.return_value = {
        "airlineName": f"Airline {airline_id}",
        "airlineNameEn": f"Airline {airline_id} En",
        "country": "KR",
        "alliance": "Star Alliance",
        "type": "FSC",
        "averageRatings": {"overall": rating},
        "totalReviews": review_count,
        "logoUrl": "http://example.com/logo.png"
    }
    return mock_doc

# Scenario:
# A: 5.0 rating, 1 review (Should be penalized)
# B: 4.5 rating, 100 reviews (Should be high)
# C: 4.8 rating, 50 reviews (Should be top if C balance is right)
# D: 4.0 rating, 1000 reviews (High count but lower rating)

mock_docs = [
    create_mock_doc("A", 1, 5.0),
    create_mock_doc("B", 100, 4.5),
    create_mock_doc("C", 50, 4.8),
    create_mock_doc("D", 1000, 4.0),
    create_mock_doc("E", 0, 0.0), # Zero reviews
]

# Mock the stream call
# airline_service uses: airlines_collection.stream()
# airlines_collection is defined in global scope of airline_service as db.collection("airlines")
# So we need to ensure airline_service.airlines_collection.stream() returns mock_docs

mock_collection = MagicMock()
mock_collection.stream.return_value = mock_docs
airline_service.airlines_collection = mock_collection

# 4. Run Test
async def run_test():
    print("Running Weighted Rating Logic verification...")
    results = await airline_service.get_popular_airlines(limit=5)
    
    print(f"\nTotal Results: {len(results)}\n")
    # Updated print header to match frontend requirements
    print(f"{'Rank':<5} | {'Name':<15} | {'Rating':<6} | {'Logo URL'}")
    print("-" * 80)
    
    for airline in results:
        # Check if fields exist
        logo_status = "[OK]" if airline.logo_url else "[MISSING]"
        print(f"{airline.rank:<5} | {airline.name:<15} | {airline.rating:<6} | {airline.logo_url} ({logo_status})")
        
    # Basic Validation
    ranks = [r.code for r in results]
    print(f"\nOrder by Code: {ranks}")
    
    # Expected: High reviews + High rating should win.
    # C (4.8, 50) > B (4.5, 100) > D (4.0, 1000) > A (5.0, 1)
    
    top_1 = results[0]
    if top_1.code == "C":
        print("\n[PASS] Test Passed: Airline C is ranked #1")
    else:
        print(f"\n[FAIL] Test Failed: Expected C, got {top_1.code}")

if __name__ == "__main__":
    asyncio.run(run_test())
