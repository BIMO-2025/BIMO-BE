"""
Firebase 데이터 구조 확인
"""
import asyncio
from app.core.firebase import FirebaseService


async def check_ke_data():
    firebase = FirebaseService()
    firebase.initialize()
    db = firebase.db
    
    print("=" * 80)
    print("대한항공(KE) Firebase 데이터 구조 확인")
    print("=" * 80)
    
    doc = db.collection("airlines").document("KE").get()
    
    if doc.exists:
        data = doc.to_dict()
        
        print(f"\nratingBreakdown 타입: {type(data.get('ratingBreakdown'))}")
        print(f"ratingBreakdown 내용:")
        
        import json
        print(json.dumps(data.get('ratingBreakdown'), indent=2, ensure_ascii=False))
    else:
        print("문서를 찾을 수 없습니다.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(check_ke_data())
