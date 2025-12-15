"""
공항 검색용 한글/영어 Mock 데이터 시딩 스크립트
한국 사용자를 위해 한글과 영어 모두 지원하는 공항 데이터를 생성합니다.
"""

import asyncio
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase import db

# 주요 공항 데이터 (한글/영어)
AIRPORTS_DATA = [
    # 한국
    {"code": "ICN", "name_en": "Incheon International Airport", "name_ko": "인천국제공항", "city_en": "Incheon", "city_ko": "인천", "country_en": "South Korea", "country_ko": "대한민국"},
    {"code": "GMP", "name_en": "Gimpo International Airport", "name_ko": "김포국제공항", "city_en": "Seoul", "city_ko": "서울", "country_en": "South Korea", "country_ko": "대한민국"},
    {"code": "CJU", "name_en": "Jeju International Airport", "name_ko": "제주국제공항", "city_en": "Jeju", "city_ko": "제주", "country_en": "South Korea", "country_ko": "대한민국"},
    {"code": "PUS", "name_en": "Gimhae International Airport", "name_ko": "김해국제공항", "city_en": "Busan", "city_ko": "부산", "country_en": "South Korea", "country_ko": "대한민국"},
    {"code": "TAE", "name_en": "Daegu International Airport", "name_ko": "대구국제공항", "city_en": "Daegu", "city_ko": "대구", "country_en": "South Korea", "country_ko": "대한민국"},
    
    # 일본
    {"code": "NRT", "name_en": "Narita International Airport", "name_ko": "나리타국제공항", "city_en": "Tokyo", "city_ko": "도쿄", "country_en": "Japan", "country_ko": "일본"},
    {"code": "HND", "name_en": "Haneda Airport", "name_ko": "하네다공항", "city_en": "Tokyo", "city_ko": "도쿄", "country_en": "Japan", "country_ko": "일본"},
    {"code": "KIX", "name_en": "Kansai International Airport", "name_ko": "간사이국제공항", "city_en": "Osaka", "city_ko": "오사카", "country_en": "Japan", "country_ko": "일본"},
    {"code": "NGO", "name_en": "Chubu Centrair International Airport", "name_ko": "주부센트레아국제공항", "city_en": "Nagoya", "city_ko": "나고야", "country_en": "Japan", "country_ko": "일본"},
    {"code": "FUK", "name_en": "Fukuoka Airport", "name_ko": "후쿠오카공항", "city_en": "Fukuoka", "city_ko": "후쿠오카", "country_en": "Japan", "country_ko": "일본"},
    
    # 중국/홍콩/대만
    {"code": "PEK", "name_en": "Beijing Capital International Airport", "name_ko": "베이징 서우두 국제공항", "city_en": "Beijing", "city_ko": "베이징", "country_en": "China", "country_ko": "중국"},
    {"code": "PVG", "name_en": "Shanghai Pudong International Airport", "name_ko": "상하이 푸동 국제공항", "city_en": "Shanghai", "city_ko": "상하이", "country_en": "China", "country_ko": "중국"},
    {"code": "CAN", "name_en": "Guangzhou Baiyun International Airport", "name_ko": "광저우 바이윈 국제공항", "city_en": "Guangzhou", "city_ko": "광저우", "country_en": "China", "country_ko": "중국"},
    {"code": "HKG", "name_en": "Hong Kong International Airport", "name_ko": "홍콩국제공항", "city_en": "Hong Kong", "city_ko": "홍콩", "country_en": "Hong Kong", "country_ko": "홍콩"},
    {"code": "TPE", "name_en": "Taiwan Taoyuan International Airport", "name_ko": "타이완 타오위안 국제공항", "city_en": "Taipei", "city_ko": "타이베이", "country_en": "Taiwan", "country_ko": "대만"},
    
    # 동남아시아
    {"code": "SIN", "name_en": "Singapore Changi Airport", "name_ko": "싱가포르 창이공항", "city_en": "Singapore", "city_ko": "싱가포르", "country_en": "Singapore", "country_ko": "싱가포르"},
    {"code": "BKK", "name_en": "Suvarnabhumi Airport", "name_ko": "수완나품공항", "city_en": "Bangkok", "city_ko": "방콕", "country_en": "Thailand", "country_ko": "태국"},
    {"code": "KUL", "name_en": "Kuala Lumpur International Airport", "name_ko": "쿠알라룸푸르 국제공항", "city_en": "Kuala Lumpur", "city_ko": "쿠알라룸푸르", "country_en": "Malaysia", "country_ko": "말레이시아"},
    {"code": "CGK", "name_en": "Soekarno-Hatta International Airport", "name_ko": "수카르노하타 국제공항", "city_en": "Jakarta", "city_ko": "자카르타", "country_en": "Indonesia", "country_ko": "인도네시아"},
    {"code": "MNL", "name_en": "Ninoy Aquino International Airport", "name_ko": "니노이 아퀴노 국제공항", "city_en": "Manila", "city_ko": "마닐라", "country_en": "Philippines", "country_ko": "필리핀"},
    {"code": "SGN", "name_en": "Tan Son Nhat International Airport", "name_ko": "떤선녓 국제공항", "city_en": "Ho Chi Minh City", "city_ko": "호치민", "country_en": "Vietnam", "country_ko": "베트남"},
    
    # 중동
    {"code": "DXB", "name_en": "Dubai International Airport", "name_ko": "두바이국제공항", "city_en": "Dubai", "city_ko": "두바이", "country_en": "UAE", "country_ko": "아랍에미리트"},
    {"code": "DOH", "name_en": "Hamad International Airport", "name_ko": "하마드국제공항", "city_en": "Doha", "city_ko": "도하", "country_en": "Qatar", "country_ko": "카타르"},
    {"code": "AUH", "name_en": "Abu Dhabi International Airport", "name_ko": "아부다비국제공항", "city_en": "Abu Dhabi", "city_ko": "아부다비", "country_en": "UAE", "country_ko": "아랍에미리트"},
    {"code": "IST", "name_en": "Istanbul Airport", "name_ko": "이스탄불공항", "city_en": "Istanbul", "city_ko": "이스탄불", "country_en": "Turkey", "country_ko": "터키"},
    
    # 북미
    {"code": "JFK", "name_en": "John F. Kennedy International Airport", "name_ko": "존 F. 케네디 국제공항", "city_en": "New York", "city_ko": "뉴욕", "country_en": "USA", "country_ko": "미국"},
    {"code": "LAX", "name_en": "Los Angeles International Airport", "name_ko": "로스앤젤레스 국제공항", "city_en": "Los Angeles", "city_ko": "로스앤젤레스", "country_en": "USA", "country_ko": "미국"},
    {"code": "ORD", "name_en": "O'Hare International Airport", "name_ko": "오헤어 국제공항", "city_en": "Chicago", "city_ko": "시카고", "country_en": "USA", "country_ko": "미국"},
    {"code": "ATL", "name_en": "Hartsfield-Jackson Atlanta International Airport", "name_ko": "하츠필드잭슨 애틀랜타 국제공항", "city_en": "Atlanta", "city_ko": "애틀랜타", "country_en": "USA", "country_ko": "미국"},
    {"code": "SFO", "name_en": "San Francisco International Airport", "name_ko": "샌프란시스코 국제공항", "city_en": "San Francisco", "city_ko": "샌프란시스코", "country_en": "USA", "country_ko": "미국"},
    {"code": "MIA", "name_en": "Miami International Airport", "name_ko": "마이애미 국제공항", "city_en": "Miami", "city_ko": "마이애미", "country_en": "USA", "country_ko": "미국"},
    {"code": "SEA", "name_en": "Seattle-Tacoma International Airport", "name_ko": "시애틀 타코마 국제공항", "city_en": "Seattle", "city_ko": "시애틀", "country_en": "USA", "country_ko": "미국"},
    {"code": "DFW", "name_en": "Dallas/Fort Worth International Airport", "name_ko": "댈러스 포트워스 국제공항", "city_en": "Dallas", "city_ko": "댈러스", "country_en": "USA", "country_ko": "미국"},
    {"code": "LAS", "name_en": "McCarran International Airport", "name_ko": "맥캐런 국제공항", "city_en": "Las Vegas", "city_ko": "라스베이거스", "country_en": "USA", "country_ko": "미국"},
    {"code": "BOS", "name_en": "Logan International Airport", "name_ko": "로건 국제공항", "city_en": "Boston", "city_ko": "보스턴", "country_en": "USA", "country_ko": "미국"},
    {"code": "YYZ", "name_en": "Toronto Pearson International Airport", "name_ko": "토론토 피어슨 국제공항", "city_en": "Toronto", "city_ko": "토론토", "country_en": "Canada", "country_ko": "캐나다"},
    {"code": "YVR", "name_en": "Vancouver International Airport", "name_ko": "밴쿠버 국제공항", "city_en": "Vancouver", "city_ko": "밴쿠버", "country_en": "Canada", "country_ko": "캐나다"},
    
    # 유럽
    {"code": "LHR", "name_en": "London Heathrow Airport", "name_ko": "런던 히드로공항", "city_en": "London", "city_ko": "런던", "country_en": "United Kingdom", "country_ko": "영국"},
    {"code": "CDG", "name_en": "Charles de Gaulle Airport", "name_ko": "샤를 드 골 공항", "city_en": "Paris", "city_ko": "파리", "country_en": "France", "country_ko": "프랑스"},
    {"code": "AMS", "name_en": "Amsterdam Airport Schiphol", "name_ko": "암스테르담 스키폴공항", "city_en": "Amsterdam", "city_ko": "암스테르담", "country_en": "Netherlands", "country_ko": "네덜란드"},
    {"code": "FRA", "name_en": "Frankfurt Airport", "name_ko": "프랑크푸르트공항", "city_en": "Frankfurt", "city_ko": "프랑크푸르트", "country_en": "Germany", "country_ko": "독일"},
    {"code": "MAD", "name_en": "Madrid-Barajas Airport", "name_ko": "마드리드 바라하스공항", "city_en": "Madrid", "city_ko": "마드리드", "country_en": "Spain", "country_ko": "스페인"},
    {"code": "FCO", "name_en": "Leonardo da Vinci-Fiumicino Airport", "name_ko": "레오나르도 다 빈치 피우미치노공항", "city_en": "Rome", "city_ko": "로마", "country_en": "Italy", "country_ko": "이탈리아"},
    {"code": "MUC", "name_en": "Munich Airport", "name_ko": "뮌헨공항", "city_en": "Munich", "city_ko": "뮌헨", "country_en": "Germany", "country_ko": "독일"},
    {"code": "ZUR", "name_en": "Zurich Airport", "name_ko": "취리히공항", "city_en": "Zurich", "city_ko": "취리히", "country_en": "Switzerland", "country_ko": "스위스"},
    
    # 오세아니아
    {"code": "SYD", "name_en": "Sydney Kingsford Smith Airport", "name_ko": "시드니 킹스포드 스미스공항", "city_en": "Sydney", "city_ko": "시드니", "country_en": "Australia", "country_ko": "호주"},
    {"code": "MEL", "name_en": "Melbourne Airport", "name_ko": "멜버른공항", "city_en": "Melbourne", "city_ko": "멜버른", "country_en": "Australia", "country_ko": "호주"},
    {"code": "AKL", "name_en": "Auckland Airport", "name_ko": "오클랜드공항", "city_en": "Auckland", "city_ko": "오클랜드", "country_en": "New Zealand", "country_ko": "뉴질랜드"},
    
    # 추가 미국 공항들 (사진에 나온 것들)
    {"code": "BOI", "name_en": "Boise Airport (Gowen Field)", "name_ko": "보이즈 공항 (가웬 필드)", "city_en": "Boise", "city_ko": "보이시", "country_en": "USA", "country_ko": "미국"},
    {"code": "TYS", "name_en": "McGhee Tyson Airport", "name_ko": "맥기 타이슨 공항", "city_en": "Knoxville", "city_ko": "녹스빌", "country_en": "USA", "country_ko": "미국"},
    {"code": "TPA", "name_en": "Tampa International Airport", "name_ko": "탬파 국제공항", "city_en": "Tampa", "city_ko": "탬파", "country_en": "USA", "country_ko": "미국"},
    {"code": "AMA", "name_en": "Rick Husband Amarillo International Airport", "name_ko": "릭 허스번드 애머릴로 국제공항", "city_en": "Amarillo", "city_ko": "애머릴로", "country_en": "USA", "country_ko": "미국"},
    {"code": "LIH", "name_en": "Lihue Airport", "name_ko": "리나이 공항", "city_en": "Lihue", "city_ko": "리나이", "country_en": "USA", "country_ko": "미국"},
]

async def seed_airports_bilingual():
    """한글/영어 공항 데이터 시딩"""
    print("🛫 공항 검색용 한글/영어 Mock 데이터 시딩 시작...")
    print("=" * 60)
    
    collection_ref = db.collection("airports")
    created_count = 0
    updated_count = 0
    
    for airport in AIRPORTS_DATA:
        code = airport["code"]
        
        # 검색을 위해 한글과 영어를 모두 포함
        # name 필드에 한글과 영어를 모두 저장 (검색 시 둘 다 매칭)
        name = f"{airport['name_ko']} ({airport['name_en']})"
        city = f"{airport['city_ko']} ({airport['city_en']})"
        country = f"{airport['country_ko']} ({airport['country_en']})"
        
        # Firestore 문서 데이터
        airport_data = {
            "code": code,
            "name": name,
            "name_en": airport["name_en"],
            "name_ko": airport["name_ko"],
            "city": city,
            "city_en": airport["city_en"],
            "city_ko": airport["city_ko"],
            "country": country,
            "country_en": airport["country_en"],
            "country_ko": airport["country_ko"],
        }
        
        doc_ref = collection_ref.document(code)
        doc = doc_ref.get()
        
        if doc.exists:
            doc_ref.update(airport_data)
            updated_count += 1
            print(f"  ✓ {airport['name_ko']} ({code}): 업데이트 완료")
        else:
            doc_ref.set(airport_data)
            created_count += 1
            print(f"  + {airport['name_ko']} ({code}): 생성 완료")
    
    print("=" * 60)
    print(f"✅ 공항 데이터 시딩 완료!")
    print(f"   - 새로 생성: {created_count}개")
    print(f"   - 업데이트: {updated_count}개")
    print(f"   - 총 처리: {len(AIRPORTS_DATA)}개")
    print("")
    print("💡 검색 팁:")
    print("   - 한글 검색: '인천', '서울', '미국' 등으로 검색 가능")
    print("   - 영어 검색: 'Incheon', 'Seoul', 'USA' 등으로 검색 가능")
    print("   - 공항 코드: 'ICN', 'JFK' 등으로 검색 가능")

if __name__ == "__main__":
    # 비동기 실행을 위한 이벤트 루프 설정
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_airports_bilingual())








