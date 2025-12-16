"""
이미지 압축 및 Base64 변환 유틸리티
"""

from typing import List
from PIL import Image
from fastapi import UploadFile, HTTPException
import io
import base64


# 설정값
MAX_SIZE = (800, 800)  # 최대 크기 (픽셀)
QUALITY = 85  # JPEG 품질 (1-100)
MAX_BASE64_SIZE = 700 * 1024  # 약 700KB (Firestore 1MB 제한 고려)
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'}


async def convert_image_to_base64(file: UploadFile) -> str:
    """
    이미지 파일을 압축 후 Base64 Data URL로 변환합니다.
    
    Args:
        file: 업로드된 이미지 파일
        
    Returns:
        Base64 Data URL (data:image/jpeg;base64,...)
        
    Raises:
        HTTPException: 파일 형식이 잘못되었거나 처리 실패 시
    """
    try:
        # 1. 파일 확장자 확인
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ''
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다: {file_extension}. 지원 형식: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # 2. 이미지 파일 읽기
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 3. RGBA/LA/P를 RGB로 변환 (PNG transparency 처리)
        if image.mode in ('RGBA', 'LA', 'P'):
            # 흰색 배경 생성
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            # 투명도가 있으면 마스크로 사용
            if image.mode == 'RGBA':
                background.paste(image, mask=image.split()[-1])
            else:
                background.paste(image)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 4. 이미지 리사이징 (비율 유지하면서 최대 크기 제한)
        image.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
        
        # 5. JPEG로 압축
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=QUALITY, optimize=True)
        compressed_data = buffer.getvalue()
        
        # 6. Base64 인코딩
        base64_string = base64.b64encode(compressed_data).decode('utf-8')
        base64_url = f"data:image/jpeg;base64,{base64_string}"
        
        # 7. 크기 확인
        if len(base64_url) > MAX_BASE64_SIZE:
            # Windows 인코딩 문제 방지를 위해 파일명을 안전하게 처리
            safe_filename = file.filename.encode('utf-8', errors='replace').decode('utf-8') if file.filename else "unknown"
            raise HTTPException(
                status_code=400,
                detail=f"압축 후에도 이미지가 너무 큽니다: {safe_filename}. 최대 크기: {MAX_BASE64_SIZE // 1024}KB"
            )
        
        # Windows 인코딩 문제 방지를 위해 파일명을 안전하게 처리
        safe_filename = file.filename.encode('utf-8', errors='replace').decode('utf-8') if file.filename else "unknown"
        print(f"[OK] 이미지 처리 완료: {safe_filename} -> {len(base64_url) // 1024}KB (Base64)")
        
        return base64_url
        
    except HTTPException:
        raise
    except Exception as e:
        # 에러 메시지에서도 파일명과 에러를 안전하게 처리
        safe_filename = file.filename.encode('utf-8', errors='replace').decode('utf-8') if file.filename else "unknown"
        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
        raise HTTPException(
            status_code=400,
            detail=f"이미지 처리 실패 ({safe_filename}): {error_msg}"
        )


async def convert_images_to_base64(files: List[UploadFile]) -> List[str]:
    """
    여러 이미지 파일을 압축 후 Base64 Data URL 리스트로 변환합니다.
    
    Args:
        files: 업로드된 이미지 파일 리스트
        
    Returns:
        Base64 Data URL 리스트
        
    Raises:
        HTTPException: 파일 처리 실패 시
    """
    base64_images = []
    
    for file in files:
        base64_url = await convert_image_to_base64(file)
        base64_images.append(base64_url)
    
    return base64_images


__all__ = ["convert_image_to_base64", "convert_images_to_base64", "MAX_SIZE", "QUALITY", "MAX_BASE64_SIZE", "ALLOWED_EXTENSIONS"]

