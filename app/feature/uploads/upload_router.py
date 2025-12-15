"""
이미지 업로드 관련 API 라우터
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
from PIL import Image
import io
import base64

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"],
    responses={404: {"description": "Not found"}},
)


@router.post("/images/base64")
async def upload_images_as_base64(
    files: List[UploadFile] = File(...)
):
    """
    이미지를 압축 후 Base64로 인코딩하여 반환합니다.
    
    - **files**: 업로드할 이미지 파일들 (여러 개 가능)
    - 자동 압축: 최대 800x800px, 품질 85%
    - 지원 형식: jpg, jpeg, png, webp, gif
    - 반환: Base64 Data URL 리스트
    
    ### 사용 예시:
    ```python
    formData = new FormData();
    formData.append('files', imageFile);
    
    fetch('/uploads/images/base64', {
      method: 'POST',
      body: formData
    })
    ```
    
    ### 반환 형식:
    ```json
    {
      "success": true,
      "images": [
        "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
        "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
      ],
      "count": 2
    }
    ```
    """
    # 설정
    MAX_SIZE = (800, 800)  # 최대 크기 (픽셀)
    QUALITY = 85  # JPEG 품질 (1-100)
    MAX_BASE64_SIZE = 700 * 1024  # 약 700KB (Firestore 1MB 제한 고려)
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'}
    
    base64_images = []
    
    for file in files:
        try:
            # 1. 파일 확장자 확인
            file_extension = file.filename.split('.')[-1].lower()
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
                raise HTTPException(
                    status_code=400,
                    detail=f"압축 후에도 이미지가 너무 큽니다: {file.filename}. 최대 크기: {MAX_BASE64_SIZE // 1024}KB"
                )
            
            base64_images.append(base64_url)
            
            print(f"✓ 이미지 처리 완료: {file.filename} → {len(base64_url) // 1024}KB (Base64)")
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"이미지 처리 실패 ({file.filename}): {str(e)}"
            )
    
    return {
        "success": True,
        "images": base64_images,
        "count": len(base64_images),
        "message": f"{len(base64_images)}개의 이미지가 성공적으로 처리되었습니다."
    }
