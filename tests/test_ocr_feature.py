"""
OCR 기능 테스트 스크립트
Gemini API를 사용하여 이미지에서 텍스트를 추출하는 기능을 테스트합니다.
"""

import os
import sys
import asyncio
import base64
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import requests


def create_test_boarding_pass_image() -> bytes:
    """
    테스트용 탑승권 이미지를 생성합니다.
    """
    # 800x400 크기의 흰색 배경 이미지 생성
    width, height = 800, 400
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 기본 폰트 사용 (시스템에 따라 다를 수 있음)
    try:
        # Windows의 경우
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_medium = ImageFont.truetype("arial.ttf", 30)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except:
        # 기본 폰트 사용
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 배경색 추가 (하늘색)
    draw.rectangle([0, 0, width, 100], fill='#1E90FF')
    
    # 항공사 이름
    draw.text((20, 20), "KOREAN AIR", fill='white', font=font_large)
    
    # 구분선
    draw.line([0, 100, width, 100], fill='#1E90FF', width=3)
    
    # 탑승권 정보
    y_offset = 130
    line_height = 45
    
    info_text = [
        "PASSENGER: KIM MINSU",
        "FLIGHT: KE001",
        "FROM: ICN (Seoul Incheon)",
        "TO: JFK (New York)",
        "DATE: 2025-12-20",
        "SEAT: 12A",
        "CLASS: Economy",
    ]
    
    for text in info_text:
        draw.text((40, y_offset), text, fill='black', font=font_small)
        y_offset += line_height
    
    # 이미지를 바이트로 변환
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def create_simple_text_image() -> bytes:
    """
    간단한 텍스트 이미지를 생성합니다.
    """
    width, height = 600, 300
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 50)
    except:
        font = ImageFont.load_default()
    
    # 텍스트 추가
    draw.text((50, 100), "Hello, OCR Test!", fill='black', font=font)
    draw.text((50, 180), "Korean Air Flight KE001", fill='blue', font=font)
    
    # 이미지를 바이트로 변환
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def image_bytes_to_base64(image_bytes: bytes) -> str:
    """
    이미지 바이트를 Base64 문자열로 변환합니다.
    """
    return base64.b64encode(image_bytes).decode('utf-8')


def test_ocr_with_api(image_bytes: bytes, prompt: str, server_url: str = "http://127.0.0.1:8000"):
    """
    LLM API를 통해 OCR 테스트를 수행합니다.
    """
    print(f"\n{'='*60}")
    print("[OCR Test] 테스트 시작")
    print(f"{'='*60}")
    
    # 이미지를 Base64로 인코딩
    base64_data = image_bytes_to_base64(image_bytes)
    print(f"[OK] 이미지 Base64 인코딩 완료 (크기: {len(base64_data)} 문자)")
    
    # API 요청 데이터 구성
    request_data = {
        "prompt": prompt,
        "images": [
            {
                "mime_type": "image/png",
                "base64_data": base64_data
            }
        ]
    }
    
    # API 호출
    print(f"\n[API] 요청 중: {server_url}/llm/chat")
    try:
        response = requests.post(
            f"{server_url}/llm/chat",
            json=request_data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\n{'='*60}")
        print("[RESULT] OCR 결과")
        print(f"{'='*60}")
        print(f"모델: {result.get('model', 'N/A')}")
        print(f"\n내용:\n{result.get('content', 'N/A')}")
        print(f"{'='*60}\n")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] API 요청 실패: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답 상태 코드: {e.response.status_code}")
            print(f"응답 내용: {e.response.text}")
        return None


def main():
    """
    메인 테스트 함수
    """
    print("\n" + "="*60)
    print("Gemini OCR 기능 테스트")
    print("="*60)
    
    # 서버 URL (필요시 수정)
    server_url = "http://127.0.0.1:8000"
    
    # 1. 간단한 텍스트 이미지 테스트
    print("\n[테스트 1] 간단한 텍스트 이미지")
    simple_image = create_simple_text_image()
    test_ocr_with_api(
        simple_image,
        "이 이미지에서 보이는 모든 텍스트를 추출해주세요.",
        server_url
    )
    
    # 2. 탑승권 이미지 테스트
    print("\n[테스트 2] 탑승권 이미지 분석")
    boarding_pass = create_test_boarding_pass_image()
    test_ocr_with_api(
        boarding_pass,
        "이 탑승권 이미지를 분석해서 항공사, 항공편 번호, 출발지, 도착지, 좌석 등급, 탑승객 이름을 추출해주세요.",
        server_url
    )
    
    # 3. 탑승권 + 리뷰 요청 테스트
    print("\n[테스트 3] 탑승권 기반 리뷰 생성")
    test_ocr_with_api(
        boarding_pass,
        "이 탑승권을 분석하고, 해당 항공사(Korean Air)의 이코노미 클래스에 대한 일반적인 리뷰와 여행 팁을 제공해주세요.",
        server_url
    )
    
    print("\n" + "="*60)
    print("[DONE] 모든 테스트 완료!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

