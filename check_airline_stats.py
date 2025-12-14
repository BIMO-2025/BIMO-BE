"""
항공사 통계 데이터 간단 확인
"""
import os
import sys
from dotenv import load_dotenv

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.core.firebase import FirebaseService


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("항공사 통계 데이터 확인")
    print("=" * 80)
    
    # Firebase 서비스 초기화
    firebase_service = FirebaseService()
    firebase_service.initialize()
    db = firebase_service.db
    
    airlines_collection = db.collection("airlines")
    
    # Korean Air (KE) 확인
    test_codes = ["KE", "OZ", "7C", "AA", "SQ"]
    
    for airline_code in test_codes:
        doc_ref = airlines_collection.document(airline_code)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            print(f"\n{airline_code} ({data.get('airlineName')}):")
            print(f"  totalReviews: {data.get('totalReviews', 0)}개")
            print(f"  overallRating: {data.get('overallRating', 0.0)}")
            print(f"  averageRatings: {data.get('averageRatings', {})}")
        else:
            print(f"\n{airline_code}: 데이터 없음")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
