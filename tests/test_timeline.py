import requests
import json

url = "http://localhost:8000/wellness/flight-timeline"
payload = {
    "origin": "DXB",
    "destination": "ICN",
    "departure_time": "2025-11-25T09:00:00",
    "arrival_time": "2025-11-25T23:15:00",
    "seat_class": "ECONOMY",
    "flight_goal": "SLEEP_FOCUS",
    "total_duration": "14h 15m"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
