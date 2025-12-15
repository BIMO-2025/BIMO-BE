"""
통합 엔드포인트 테스트
"""
import asyncio
import httpx
import json


async def test_integrated_endpoint():
    print("=" * 80)
    print("통합 엔드포인트 테스트: /airlines/KE")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n항공사 상세 정보 조회 중...")
        
        try:
            response = await client.get("http://localhost:8000/airlines/KE")
            
            print(f"\nStatus Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n✅ 항공사: {data.get('airlineName', 'N/A')}")
                print(f"✅ 전체 평점: {data.get('overallRating', 0)}/5.0")
                print(f"✅ 총 리뷰 수: {data.get('totalReviews', 0)}개")
                
                print(f"\n📊 카테고리별 평점:")
                avg_ratings = data.get('averageRatings', {})
                for key, value in avg_ratings.items():
                    print(f"  - {key}: {value}")
                
                print(f"\n✨ BIMO 요약:")
                bimo = data.get('bimoSummary')
                if bimo:
                    good_points = bimo.get('goodPoints', [])
                    bad_points = bimo.get('badPoints', [])
                    
                    print(f"\n  Good Points ({len(good_points)}개):")
                    for i, point in enumerate(good_points, 1):
                        print(f"    {i}. {point}")
                    
                    print(f"\n  Bad Points ({len(bad_points)}개):")
                    for i, point in enumerate(bad_points, 1):
                        print(f"    {i}. {point}")
                    
                    print(f"\n  리뷰 개수: {bimo.get('reviewCount', 0)}")
                    print(f"  마지막 업데이트: {bimo.get('lastUpdated', 'N/A')}")
                else:
                    print("  ⚠️  BIMO 요약이 아직 생성되지 않았습니다.")
                    print("  (리뷰가 추가/수정/삭제되면 백그라운드에서 생성됩니다)")
                
            else:
                print(f"\n❌ 오류: {response.text}")
        
        except Exception as e:
            print(f"\n❌ 예외 발생: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_integrated_endpoint())
