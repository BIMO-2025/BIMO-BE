"""
항공사 데이터 시딩 스크립트
주요 항공사 정보를 Firestore에 미리 저장합니다.
"""

import asyncio
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase import db
from app.feature.flights.flights_schemas import AirlineSchema

async def seed_airlines():
    print("🛫 항공사 데이터 시딩 시작...")
    
    # 주요 항공사 목록 (IATA 코드)
    # 로고 URL: https://pics.avs.io/200/200/{IATA}.png
    airlines_data = [
        # --- 대한민국 (Korea) ---
        {"code": "KE", "name": "Korean Air"},
        {"code": "OZ", "name": "Asiana Airlines"},
        {"code": "7C", "name": "Jeju Air"},
        {"code": "LJ", "name": "Jin Air"},
        {"code": "TW", "name": "T'way Air"},
        {"code": "BX", "name": "Air Busan"},
        {"code": "RS", "name": "Air Seoul"},
        {"code": "ZE", "name": "Eastar Jet"},
        {"code": "RF", "name": "Aero K"},
        {"code": "YP", "name": "Air Premia"},

        # --- 아시아 (Asia) ---
        {"code": "JL", "name": "Japan Airlines"},
        {"code": "NH", "name": "All Nippon Airways (ANA)"},
        {"code": "MM", "name": "Peach Aviation"},
        {"code": "7G", "name": "StarFlyer"},
        {"code": "BC", "name": "Skymark Airlines"},
        {"code": "CX", "name": "Cathay Pacific"},
        {"code": "UO", "name": "HK Express"},
        {"code": "HX", "name": "Hong Kong Airlines"},
        {"code": "SQ", "name": "Singapore Airlines"},
        {"code": "TR", "name": "Scoot"},
        {"code": "CI", "name": "China Airlines"},
        {"code": "BR", "name": "EVA Air"},
        {"code": "JX", "name": "STARLUX Airlines"},
        {"code": "VN", "name": "Vietnam Airlines"},
        {"code": "VJ", "name": "VietJet Air"},
        {"code": "QH", "name": "Bamboo Airways"},
        {"code": "TG", "name": "Thai Airways"},
        {"code": "FD", "name": "Thai AirAsia"},
        {"code": "XJ", "name": "Thai AirAsia X"},
        {"code": "MH", "name": "Malaysia Airlines"},
        {"code": "AK", "name": "AirAsia"},
        {"code": "D7", "name": "AirAsia X"},
        {"code": "GA", "name": "Garuda Indonesia"},
        {"code": "5J", "name": "Cebu Pacific"},
        {"code": "PR", "name": "Philippine Airlines"},
        {"code": "CA", "name": "Air China"},
        {"code": "MU", "name": "China Eastern Airlines"},
        {"code": "CZ", "name": "China Southern Airlines"},
        {"code": "AI", "name": "Air India"},
        {"code": "6E", "name": "IndiGo"},

        # --- 중동 (Middle East) ---
        {"code": "EK", "name": "Emirates"},
        {"code": "QR", "name": "Qatar Airways"},
        {"code": "EY", "name": "Etihad Airways"},
        {"code": "TK", "name": "Turkish Airlines"},
        {"code": "SV", "name": "Saudia"},
        {"code": "LY", "name": "El Al Israel Airlines"},

        # --- 북미 (North America) ---
        {"code": "DL", "name": "Delta Air Lines"},
        {"code": "AA", "name": "American Airlines"},
        {"code": "UA", "name": "United Airlines"},
        {"code": "AC", "name": "Air Canada"},
        {"code": "WS", "name": "WestJet"},
        {"code": "AS", "name": "Alaska Airlines"},
        {"code": "B6", "name": "JetBlue Airways"},
        {"code": "WN", "name": "Southwest Airlines"},
        {"code": "NK", "name": "Spirit Airlines"},
        {"code": "F9", "name": "Frontier Airlines"},
        {"code": "HA", "name": "Hawaiian Airlines"},

        # --- 유럽 (Europe) ---
        {"code": "AF", "name": "Air France"},
        {"code": "KL", "name": "KLM Royal Dutch Airlines"},
        {"code": "LH", "name": "Lufthansa"},
        {"code": "BA", "name": "British Airways"},
        {"code": "VS", "name": "Virgin Atlantic"},
        {"code": "IB", "name": "Iberia"},
        {"code": "AY", "name": "Finnair"},
        {"code": "SK", "name": "SAS Scandinavian Airlines"},
        {"code": "LX", "name": "Swiss International Air Lines"},
        {"code": "OS", "name": "Austrian Airlines"},
        {"code": "LO", "name": "LOT Polish Airlines"},
        {"code": "AZ", "name": "ITA Airways"},
        {"code": "FR", "name": "Ryanair"},
        {"code": "U2", "name": "easyJet"},
        {"code": "W6", "name": "Wizz Air"},
        {"code": "VY", "name": "Vueling Airlines"},
        {"code": "DY", "name": "Norwegian Air Shuttle"},
        {"code": "EI", "name": "Aer Lingus"},
        {"code": "TP", "name": "TAP Air Portugal"},
        {"code": "SU", "name": "Aeroflot"},

        # --- 오세아니아 (Oceania) ---
        {"code": "QF", "name": "Qantas"},
        {"code": "JQ", "name": "Jetstar Airways"},
        {"code": "VA", "name": "Virgin Australia"},
        {"code": "NZ", "name": "Air New Zealand"},

        # --- 남미 (South America) ---
        {"code": "LA", "name": "LATAM Airlines"},
        {"code": "AR", "name": "Aerolineas Argentinas"},
        {"code": "AV", "name": "Avianca"},
        {"code": "G3", "name": "Gol Transportes Aereos"},
        {"code": "AM", "name": "Aeromexico"},
    ]
    
    collection_ref = db.collection("airlines")
    
    for airline in airlines_data:
        iata_code = airline["code"]
        name = airline["name"]
        logo_url = f"https://pics.avs.io/200/200/{iata_code}.png"
        
        doc_ref = collection_ref.document(iata_code)
        doc = doc_ref.get()
        
        if doc.exists:
            print(f"  - {name} ({iata_code}): 이미 존재함 (업데이트 생략)")
            # 필요하다면 여기서 업데이트 로직 추가
            # doc_ref.update({"logoUrl": logo_url, "iataCode": iata_code})
        else:
            new_airline = AirlineSchema(
                airlineName=name,
                iataCode=iata_code,
                logoUrl=logo_url,
                totalReviews=0
            )
            doc_ref.set(new_airline.model_dump())
            print(f"  + {name} ({iata_code}): 생성 완료")
            
    print("✅ 항공사 데이터 시딩 완료!")

if __name__ == "__main__":
    # 비동기 실행을 위한 이벤트 루프 설정
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_airlines())
