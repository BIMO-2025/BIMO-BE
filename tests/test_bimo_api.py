"""
BIMO 요약 API 테스트
"""
import asyncio
import httpx
import json


async def main():
    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("대한항공 BIMO 요약 API 조회")
        print("=" * 80)
        
        response = await client.get("http://localhost:8000/airlines/KE/summary")
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nAirline: {data.get('airline_name', 'N/A')}")
            print(f"Review Count: {data.get('review_count', 0)}")
            
            print(f"\n✓ Good Points ({len(data.get('good_points', []))}개):")
            for i, point in enumerate(data.get("good_points", []), 1):
                print(f"  {i}. {point}")
            
            print(f"\n✓ Bad Points ({len(data.get('bad_points', []))}개):")
            for i, point in enumerate(data.get("bad_points", []), 1):
                print(f"  {i}. {point}")
        else:
            print(f"\n오류: {response.text}")
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
