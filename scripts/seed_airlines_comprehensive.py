"""
항공사 종합 Mock 데이터 시딩 스크립트
이미지 URL, 상세 정보, 허브 공항 등 모든 정보를 포함한 데이터를 생성합니다.
"""

import asyncio
import sys
import os
import random

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase import db

# 항공 동맹 정보
ALLIANCES = {
    "Star Alliance": ["KE", "OZ", "NH", "SQ", "TG", "CA", "UA", "LH", "AC", "SK", "LX", "OS", "TP"],
    "SkyTeam": ["KE", "OZ", "DL", "AF", "KL", "CI", "CZ", "MU", "SU", "AM", "AZ", "VS"],
    "oneworld": ["JL", "CX", "BA", "AA", "QF", "IB", "AY", "QR"],
}

# 국가 정보 매핑
COUNTRY_MAP = {
    # 한국
    "KE": "Korea", "OZ": "Korea", "7C": "Korea", "LJ": "Korea", "TW": "Korea",
    "BX": "Korea", "RS": "Korea", "ZE": "Korea", "RF": "Korea", "YP": "Korea",
    # 일본
    "JL": "Japan", "NH": "Japan", "MM": "Japan", "7G": "Japan", "BC": "Japan",
    # 중국/홍콩/대만
    "CX": "Hong Kong", "UO": "Hong Kong", "HX": "Hong Kong",
    "CI": "Taiwan", "BR": "Taiwan", "JX": "Taiwan",
    "CA": "China", "MU": "China", "CZ": "China",
    # 동남아
    "SQ": "Singapore", "TR": "Singapore",
    "VN": "Vietnam", "VJ": "Vietnam", "QH": "Vietnam",
    "TG": "Thailand", "FD": "Thailand", "XJ": "Thailand",
    "MH": "Malaysia", "AK": "Malaysia", "D7": "Malaysia",
    "GA": "Indonesia",
    "5J": "Philippines", "PR": "Philippines",
    # 남아시아
    "AI": "India", "6E": "India",
    # 중동
    "EK": "UAE", "QR": "Qatar", "EY": "UAE", "TK": "Turkey", "SV": "Saudi Arabia", "LY": "Israel",
    # 북미
    "DL": "USA", "AA": "USA", "UA": "USA", "AS": "USA", "B6": "USA", "WN": "USA", "NK": "USA", "F9": "USA", "HA": "USA",
    "AC": "Canada", "WS": "Canada",
    # 유럽
    "AF": "France", "KL": "Netherlands", "LH": "Germany", "BA": "United Kingdom", "VS": "United Kingdom",
    "IB": "Spain", "AY": "Finland", "SK": "Sweden", "LX": "Switzerland", "OS": "Austria",
    "LO": "Poland", "AZ": "Italy", "FR": "Ireland", "U2": "United Kingdom", "W6": "Hungary",
    "VY": "Spain", "DY": "Norway", "EI": "Ireland", "TP": "Portugal", "SU": "Russia",
    # 오세아니아
    "QF": "Australia", "JQ": "Australia", "VA": "Australia", "NZ": "New Zealand",
    # 남미
    "LA": "Chile", "AR": "Argentina", "AV": "Colombia", "G3": "Brazil", "AM": "Mexico",
}

# 허브 공항 정보
HUB_AIRPORTS = {
    "KE": "ICN", "OZ": "ICN", "JL": "NRT", "NH": "NRT", "SQ": "SIN", "CX": "HKG",
    "EK": "DXB", "QR": "DOH", "EY": "AUH", "DL": "ATL", "AA": "DFW", "UA": "ORD",
    "AF": "CDG", "KL": "AMS", "LH": "FRA", "BA": "LHR", "QF": "SYD", "AC": "YYZ",
}

# 항공사 타입 (FSC vs LCC)
AIRLINE_TYPES = {
    "FSC": ["KE", "OZ", "JL", "NH", "CX", "SQ", "EK", "QR", "DL", "AA", "UA", "AF", "KL", "LH", "BA", "QF"],
    "LCC": ["7C", "LJ", "TW", "BX", "RS", "ZE", "MM", "TR", "VJ", "FD", "AK", "D7", "5J", "6E", "FR", "U2", "W6"],
}

# Mock 설명 텍스트 템플릿
DESCRIPTION_TEMPLATE = "{name} is a {type} airline based in {country}. Known for {feature}."

def get_alliance(code: str) -> str:
    """항공사 코드로 동맹 찾기"""
    for alliance, codes in ALLIANCES.items():
        if code in codes:
            return alliance
    return None

def get_country(code: str) -> str:
    """항공사 코드로 국가 찾기"""
    return COUNTRY_MAP.get(code, "Unknown")

def get_hub_airport(code: str) -> str:
    """항공사 코드로 허브 공항 찾기"""
    return HUB_AIRPORTS.get(code)

def get_airline_type(code: str) -> str:
    """항공사 코드로 타입 찾기"""
    if code in AIRLINE_TYPES["FSC"]:
        return "FSC"
    elif code in AIRLINE_TYPES["LCC"]:
        return "LCC"
    else:
        return "FSC"  # 기본값

def generate_description(name: str, country: str, airline_type: str) -> str:
    """항공사 설명 생성"""
    features = [
        "excellent service and comfortable seating",
        "modern fleet and reliable operations",
        "competitive pricing and convenient schedules",
        "luxury amenities and premium experience",
        "extensive route network",
    ]
    feature = random.choice(features)
    return DESCRIPTION_TEMPLATE.format(
        name=name,
        type=airline_type,
        country=country,
        feature=feature
    )

def generate_images(code: str, name: str) -> list:
    """항공사 관련 이미지 URL 생성"""
    # 실제 이미지 URL 사용 (avs.io 또는 unsplash 등)
    logo_url = f"https://pics.avs.io/200/200/{code}.png"
    
    # 추가 이미지들 (항공사 비행기, 캐빈 등)
    images = [
        logo_url,
        f"https://pics.avs.io/400/200/{code}.png",  # 큰 로고
    ]
    
    # 랜덤 항공기 이미지 (Unsplash 사용)
    aircraft_images = [
        "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800",
        "https://images.unsplash.com/photo-1586348943529-beaae6c28db9?w=800",
        "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=800",
        "https://images.unsplash.com/photo-1529107386315-e3a1b8e50b90?w=800",
    ]
    images.extend(random.sample(aircraft_images, 2))
    
    return images

async def seed_airlines_comprehensive():
    """종합 항공사 데이터 시딩"""
    print("🛫 항공사 종합 Mock 데이터 시딩 시작...")
    print("=" * 60)
    
    # 주요 항공사 목록 (IATA 코드)
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
    created_count = 0
    updated_count = 0
    
    for airline in airlines_data:
        code = airline["code"]
        name = airline["name"]
        
        country = get_country(code)
        alliance = get_alliance(code)
        airline_type = get_airline_type(code)
        hub_airport = get_hub_airport(code)
        description = generate_description(name, country, airline_type)
        images = generate_images(code, name)
        logo_url = f"https://pics.avs.io/200/200/{code}.png"
        
        # 평점 생성 (3.5 ~ 4.8 사이, 소수점 1자리)
        rating = round(random.uniform(3.5, 4.8), 1)
        
        # 리뷰 수 생성 (0 ~ 500 사이)
        review_count = random.randint(0, 500)
        
        # 허브 공항 이름 매핑
        hub_airport_names = {
            "ICN": "인천국제공항", "NRT": "나리타국제공항", "SIN": "싱가포르 창이공항",
            "HKG": "홍콩국제공항", "DXB": "두바이국제공항", "DOH": "도하 하마드국제공항",
            "ATL": "하츠필드잭슨 애틀랜타 국제공항", "DFW": "댈러스 포트워스 국제공항",
            "ORD": "오헤어 국제공항", "CDG": "파리 샤를 드골공항", "AMS": "암스테르담 스키폴공항",
            "FRA": "프랑크푸르트공항", "LHR": "런던 히드로공항", "SYD": "시드니 킹스포드 스미스공항",
            "YYZ": "토론토 피어슨 국제공항",
        }
        
        # 운항 클래스 설정
        operating_classes_map = {
            "FSC": ["이코노미", "프리미엄 이코노미", "비즈니스", "퍼스트"],
            "LCC": ["이코노미"],
        }
        operating_classes = operating_classes_map.get(airline_type, ["이코노미"])
        
        # 영어 이름 매핑 (주요 항공사)
        airline_name_en_map = {
            "KE": "Korean Air", "OZ": "Asiana Airlines", "JL": "Japan Airlines",
            "NH": "All Nippon Airways", "SQ": "Singapore Airlines", "CX": "Cathay Pacific",
            "EK": "Emirates", "QR": "Qatar Airways", "EY": "Etihad Airways",
            "DL": "Delta Air Lines", "AA": "American Airlines", "UA": "United Airlines",
            "AF": "Air France", "KL": "KLM Royal Dutch Airlines", "LH": "Lufthansa",
            "BA": "British Airways", "QF": "Qantas", "AC": "Air Canada",
        }
        
        # Firestore 문서 데이터 (AirlineSchema 형식)
        airline_data = {
            "airlineName": name,
            "airlineNameEn": AIRLINE_NAMES_EN.get(code),
            "country": country,
            "type": airline_type,
            "logoUrl": logo_url,
            "description": description,
            "images": images,
            "operatingClasses": operating_classes,
            # 집계 통계 필드 (초기값)
            "totalReviews": 0,
            "totalRatingSums": {
                "seatComfort": 0,
                "inflightMeal": 0,
                "service": 0,
                "cleanliness": 0,
                "checkIn": 0,
            },
            "averageRatings": {
                "seatComfort": 0.0,
                "inflightMeal": 0.0,
                "service": 0.0,
                "cleanliness": 0.0,
                "checkIn": 0.0,
            },
            "ratingBreakdown": {
                "seatComfort": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                "inflightMeal": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                "service": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                "cleanliness": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                "checkIn": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
            },
            "overallRating": 0.0,
        }
        
        # 선택적 필드 추가
        if alliance:
            airline_data["alliance"] = alliance
        if hub_airport:
            airline_data["hubAirport"] = hub_airport
            airline_data["hubAirportName"] = hub_airport_names.get(hub_airport)
        
        doc_ref = collection_ref.document(code)
        doc = doc_ref.get()
        
        if doc.exists:
            # 기존 문서 업데이트
            doc_ref.update(airline_data)
            updated_count += 1
            print(f"  ✓ {name} ({code}): 업데이트 완료")
        else:
            # 새 문서 생성
            doc_ref.set(airline_data)
            created_count += 1
            print(f"  + {name} ({code}): 생성 완료")
    
    print("=" * 60)
    print(f"✅ 항공사 데이터 시딩 완료!")
    print(f"   - 새로 생성: {created_count}개")
    print(f"   - 업데이트: {updated_count}개")
    print(f"   - 총 처리: {len(airlines_data)}개")

if __name__ == "__main__":
    # 비동기 실행을 위한 이벤트 루프 설정
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_airlines_comprehensive())

