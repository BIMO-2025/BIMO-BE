"""
Firebase에서 직접 BIMO 요약 확인
"""
import asyncio
from app.core.firebase import FirebaseService


async def main():
    firebase = FirebaseService()
    firebase.initialize()
    db = firebase.db
    
    print("=" * 80)
    print("Firebase에서 BIMO 요약 직접 확인")
    print("=" * 80)
    
    airline_doc = db.collection("airlines").document("KE").get()
    
    if airline_doc.exists:
        data = airline_doc.to_dict()
        bimo = data.get("bimoSummary", {})
        
        print(f"\n✓ BIMO 요약 발견!")
        print(f"\nGood Points ({len(bimo.get('goodPoints', []))}개):")
        for i, point in enumerate(bimo.get("goodPoints", []), 1):
            print(f"  {i}. {point}")
        
        print(f"\nBad Points ({len(bimo.get('badPoints', []))}개):")
        for i, point in enumerate(bimo.get("badPoints", []), 1):
            print(f"  {i}. {point}")
        
        print(f"\n리뷰 개수: {bimo.get('reviewCount', 0)}")
        print(f"마지막 업데이트: {bimo.get('lastUpdated', 'N/A')}")
    else:
        print("\n✗ 항공사 문서를 찾을 수 없습니다.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
