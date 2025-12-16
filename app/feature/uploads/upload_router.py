"""
이미지 업로드 관련 API 라우터
"""

from fastapi import APIRouter, File, UploadFile
from typing import List

from app.core.image_utils import convert_images_to_base64

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
    base64_images = await convert_images_to_base64(files)
    
    return {
        "success": True,
        "images": base64_images,
        "count": len(base64_images),
        "message": f"{len(base64_images)}개의 이미지가 성공적으로 처리되었습니다."
    }
