"""
리뷰 관련 API 라우터
"""
from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException, Depends, BackgroundTasks, Form, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Annotated, List
import json

from app.core.deps import get_firebase_service, get_gemini_client
from app.core.firebase import FirebaseService
from app.core.security import decode_access_token
from app.core.exceptions.exceptions import InvalidTokenError, CustomException
from app.core.image_utils import convert_images_to_base64
from app.feature.llm.gemini_client import GeminiClient
from app.feature.reviews.reviews_service import ReviewsService
from app.feature.reviews.review_verification import verify_review_with_boarding_pass
from app.feature.flights.my_flights_service import MyFlightsService
from app.feature.reviews import reviews_schemas

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()


def get_reviews_service(
    firebase_service = Depends(get_firebase_service),
    gemini_client = Depends(get_gemini_client)
) -> ReviewsService:
    """
    ReviewsService 인스턴스를 생성합니다.
    """
    return ReviewsService(
        firebase_service=firebase_service,
        gemini_client=gemini_client
    )





@router.get("/{review_id}", response_model=reviews_schemas.ReviewSchema)
async def get_review(
    review_id: str,
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    리뷰 ID로 특정 리뷰를 조회합니다.
    
    - **review_id**: 리뷰 ID
    """
    return await service.get_review_by_id(review_id)





@router.get("/detailed/{airline_code}", response_model=reviews_schemas.DetailedReviewsResponse)
async def get_detailed_reviews(
    airline_code: str,
    # 필터 파라미터
    departure_airport: Optional[str] = Query(None, description="출발 공항 코드 (예: ICN)"),
    arrival_airport: Optional[str] = Query(None, description="도착 공항 코드 (예: CDG)"),
    seat_class: Optional[str] = Query(None, description="좌석 등급: 전체, 프리미엄 이코노미, 이코노미, 비즈니스, 퍼스트"),
    period: Optional[str] = Query(None, description="기간: 전체, 최근 3개월, 최근 6개월, 최근 1년"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="최소 평점 (1~5)"),
    photo_only: Optional[bool] = Query(False, description="사진/동영상 리뷰만 보기"),
    # 정렬 및 페이지네이션
    sort: str = Query("latest", description="정렬 옵션: latest, recommended, rating_high, rating_low, likes_high"),
    limit: int = Query(20, ge=1, le=100, description="조회할 리뷰 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    항공사 상세 리뷰 페이지 정보를 조회합니다 (필터링 및 정렬 지원).
    
    ### 필터 옵션
    - **departure_airport**: 출발 공항 코드 (예: ICN)
    - **arrival_airport**: 도착 공항 코드 (예: CDG)
    - **seat_class**: 좌석 등급 (전체, 프리미엄 이코노미, 이코노미, 비즈니스, 퍼스트)
    - **period**: 기간 (전체, 최근 3개월, 최근 6개월, 최근 1년)
    - **min_rating**: 최소 평점 (1~5)
    - **photo_only**: 사진/동영상 리뷰만 보기 (true/false)
    
    ### 정렬 옵션
    - **latest**: 최신순 (기본값)
    - **recommended**: 추천순 (좋아요 많은 순)
    - **rating_high**: 평점 높은 순
    - **rating_low**: 평점 낮은 순
    - **likes_high**: 좋아요 많은 순 (recommended와 동일)
    
    ### 페이지네이션
    - **limit**: 조회할 리뷰 개수 (기본값: 20, 최대: 100)
    - **offset**: 오프셋 (기본값: 0)
    
    응답에는 전체 평점, 카테고리별 평점, 사진 리뷰 갤러리, 필터링 및 정렬된 개별 리뷰 목록이 포함됩니다.
    """
    try:
        filter_request = reviews_schemas.ReviewFilterRequest(
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            seat_class=seat_class,
            period=period,
            min_rating=min_rating,
            photo_only=photo_only
        )
        
        return await service.get_detailed_reviews_page(
            airline_code=airline_code,
            filter_request=filter_request,
            sort=sort,
            limit=limit,
            offset=offset
        )
    except HTTPException:
        # FastAPI 표준 예외는 그대로 전달
        raise
    except CustomException:
        # CustomException(DatabaseError 등)은 app-level handler에서 표준 포맷으로 처리되도록 그대로 올립니다.
        raise
    except Exception as e:
        # 그 외 알 수 없는 예외는 500으로 노출
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")


@router.post("/verify", response_model=reviews_schemas.ReviewVerificationResponse, status_code=200)
async def verify_review(
    images: List[UploadFile] = File(..., description="탑승권 이미지 파일들 (최소 1개, 최대 3개)"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    탑승권 이미지를 분석하여 사용자의 myFlights와 일치하는지 인증합니다.
    
    - **인증 필요**: Bearer Token
    - **이미지 자동 처리**: 업로드된 이미지를 자동으로 압축 후 Base64로 변환
    - OCR을 통해 탑승권 정보를 추출하고, 사용자의 myFlights와 비교하여 인증 결과를 반환합니다.
    
    **File Fields:**
    - images: 탑승권 이미지 파일들 (최소 1개, 최대 3개, jpg/png/webp 등)
    
    **Response:**
    - isVerified: true (인증 성공) 또는 false (인증 실패)
    
    **사용 예시 (JavaScript):**
    ```javascript
    const formData = new FormData();
    formData.append('images', boardingPassImageFile);
    
    fetch('/reviews/verify', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer YOUR_TOKEN' },
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      console.log('인증 결과:', data.isVerified); // true 또는 false
    });
    ```
    """
    try:
        # 토큰 검증
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        
        # 이미지 파일들을 Base64로 변환 (최대 3개)
        image_urls = []
        if images:
            images_to_convert = images[:3]  # 최대 3개만 처리
            image_urls = await convert_images_to_base64(images_to_convert)
        
        if not image_urls:
            raise HTTPException(status_code=400, detail="이미지 파일이 필요합니다.")
        
        # 탑승권 이미지로 인증 시도
        try:
            firebase_service = get_firebase_service()
            my_flights_service = MyFlightsService(firebase_service)
            verified = await verify_review_with_boarding_pass(
                user_id=user_id,
                image_urls=image_urls,
                my_flights_service=my_flights_service
            )
        except Exception as e:
            print(f"[Review Verification] 인증 프로세스 중 오류 발생: {e}")
            verified = False
        
        return reviews_schemas.ReviewVerificationResponse(isVerified=verified)
        
    except HTTPException:
        raise
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("", response_model=reviews_schemas.ReviewSchema, status_code=201)
async def create_review(
    userId: str = Form(...),
    userNickname: str = Form(...),
    airlineCode: str = Form(...),
    airlineName: str = Form(...),
    route: str = Form(...),
    text: str = Form(...),
    ratings: str = Form(..., description="JSON 형식의 평점 객체 (예: {\"seatComfort\":5,\"inflightMeal\":4,...})"),
    overallRating: float = Form(..., ge=1, le=5),
    flightNumber: Optional[str] = Form(None),
    seatClass: Optional[str] = Form(None),
    isVerified: bool = Form(False),
    likes: int = Form(0),
    images: List[UploadFile] = File(default=[]),
    background_tasks: BackgroundTasks = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    새로운 리뷰를 생성합니다 (multipart/form-data).
    
    - **인증 필요**: Bearer Token
    - **이미지 자동 처리**: 업로드된 이미지를 자동으로 압축 후 Base64로 변환하여 저장
    - 리뷰 작성 시 항공사 통계가 자동으로 업데이트됩니다 (백그라운드에서 처리)
    
    **Form Fields:**
    - userId: 사용자 ID
    - userNickname: 사용자 닉네임
    - airlineCode: 항공사 코드
    - airlineName: 항공사 이름
    - route: 노선 (예: "ICN-CDG")
    - text: 리뷰 내용
    - ratings: JSON 형식의 평점 객체 (예: {"seatComfort":5,"inflightMeal":4,"service":5,"cleanliness":4,"checkIn":5})
    - overallRating: 전체 평점 (1~5)
    - flightNumber: 항공편 번호 (선택사항)
    - seatClass: 좌석 등급 (선택사항)
    - isVerified: 인증 여부 (기본값: false)
    - likes: 좋아요 수 (기본값: 0)
    
    **File Fields:**
    - images: 리뷰 이미지 파일들 (최대 3개, jpg/png/webp 등)
    
    **사용 예시 (JavaScript):**
    ```javascript
    const formData = new FormData();
    formData.append('userId', 'user123');
    formData.append('userNickname', '여행자');
    formData.append('airlineCode', 'KE');
    formData.append('airlineName', '대한항공');
    formData.append('route', 'ICN-CDG');
    formData.append('text', '훌륭한 서비스!');
    formData.append('ratings', JSON.stringify({
      seatComfort: 5, inflightMeal: 4, service: 5, 
      cleanliness: 4, checkIn: 5
    }));
    formData.append('overallRating', 4.5);
    formData.append('images', imageFile1);
    formData.append('images', imageFile2);
    
    fetch('/reviews', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer YOUR_TOKEN' },
      body: formData
    });
    ```
    """
    try:
        # 토큰 검증
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        
        # 1. 이미지 파일들을 Base64로 변환 (최대 3개)
        image_urls = []
        if images:
            images_to_convert = images[:3]  # 최대 3개만 처리
            image_urls = await convert_images_to_base64(images_to_convert)
        
        # 2. isVerified는 클라이언트에서 전달받은 값 사용 (별도 /verify 엔드포인트 사용 권장)
        verified = isVerified
        
        # 3. ratings JSON 파싱
        try:
            ratings_dict = json.loads(ratings)
            ratings_obj = reviews_schemas.RatingsSchema(**ratings_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=400, 
                detail=f"ratings 필드가 올바른 JSON 형식이 아닙니다: {str(e)}"
            )
        
        # 4. ReviewSchema 객체 생성
        review_data = reviews_schemas.ReviewSchema(
            userId=userId,
            userNickname=userNickname,
            airlineCode=airlineCode,
            airlineName=airlineName,
            route=route,
            text=text,
            ratings=ratings_obj,
            overallRating=overallRating,
            flightNumber=flightNumber,
            seatClass=seatClass,
            isVerified=verified,  # 인증 결과 반영
            likes=likes,
            imageUrls=image_urls
        )
        
        # 4. 리뷰 생성
        created_review = await service.create_review(review_data, user_id)
        
        # 5. 백그라운드 작업
        background_tasks.add_task(
            service._update_airline_statistics,
            airlineCode
        )
        background_tasks.add_task(
            service._update_bimo_summary,
            airlineCode
        )
        
        # 6. 리뷰 객체 반환
        return created_review
        
    except HTTPException:
        raise
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{review_id}", response_model=reviews_schemas.ReviewSchema)
async def update_review(
    review_id: str,
    userId: str = Form(...),
    userNickname: str = Form(...),
    airlineCode: str = Form(...),
    airlineName: str = Form(...),
    route: str = Form(...),
    text: str = Form(...),
    ratings: str = Form(..., description="JSON 형식의 평점 객체"),
    overallRating: float = Form(..., ge=1, le=5),
    flightNumber: Optional[str] = Form(None),
    seatClass: Optional[str] = Form(None),
    isVerified: bool = Form(False),
    likes: int = Form(0),
    images: List[UploadFile] = File(default=[]),
    keep_existing_images: bool = Form(True, description="기존 이미지 유지 여부 (true: 기존 이미지 + 새 이미지 추가, false: 새 이미지로 완전 교체)"),
    background_tasks: BackgroundTasks = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    기존 리뷰를 수정합니다 (multipart/form-data).
    
    - **인증 필요**: Bearer Token (본인의 리뷰만 수정 가능)
    - **이미지 자동 처리**: 업로드된 이미지를 자동으로 압축 후 Base64로 변환
    - 리뷰 수정 시 항공사 통계가 자동으로 업데이트됩니다 (백그라운드에서 처리)
    
    **Path Parameters:**
    - review_id: 리뷰 ID
    
    **Form Fields:** create_review와 동일
    - keep_existing_images: 기존 이미지 유지 여부 (기본값: true)
      - true: 기존 이미지에 새 이미지 추가 (최대 3개까지)
      - false: 기존 이미지 삭제하고 새 이미지로 교체
    
    **File Fields:**
    - images: 추가할 이미지 파일들 (최대 3개)
    """
    try:
        # 토큰 검증
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        
        # 1. 기존 리뷰 조회
        old_review = await service.get_review_by_id(review_id)
        old_airline_code = old_review.airlineCode
        
        # 2. 이미지 처리
        image_urls = []
        
        # 기존 이미지 유지 옵션 처리
        if keep_existing_images and old_review.imageUrls:
            image_urls = list(old_review.imageUrls)  # 기존 이미지 복사
        
        # 새 이미지 추가
        if images:
            new_base64_images = await convert_images_to_base64(images)
            image_urls.extend(new_base64_images)
        
        # 최대 3개까지만 유지
        image_urls = image_urls[:3]
        
        # 2-1. isVerified는 클라이언트에서 전달받은 값 사용 (별도 /verify 엔드포인트 사용 권장)
        verified = isVerified
        
        # 3. ratings JSON 파싱
        try:
            ratings_dict = json.loads(ratings)
            ratings_obj = reviews_schemas.RatingsSchema(**ratings_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"ratings 필드가 올바른 JSON 형식이 아닙니다: {str(e)}"
            )
        
        # 4. ReviewSchema 객체 생성
        review_data = reviews_schemas.ReviewSchema(
            userId=userId,
            userNickname=userNickname,
            airlineCode=airlineCode,
            airlineName=airlineName,
            route=route,
            text=text,
            ratings=ratings_obj,
            overallRating=overallRating,
            flightNumber=flightNumber,
            seatClass=seatClass,
            isVerified=verified,  # 인증 결과 반영
            likes=likes,
            imageUrls=image_urls
        )
        
        # 5. 리뷰 수정
        updated_review = await service.update_review(review_id, review_data, user_id)
        
        # 6. 백그라운드 작업
        background_tasks.add_task(
            service._update_airline_statistics,
            airlineCode
        )
        background_tasks.add_task(
            service._update_bimo_summary,
            airlineCode
        )
        
        # 항공사 변경 시 이전 항공사도 업데이트
        if old_airline_code != airlineCode:
            background_tasks.add_task(
                service._update_airline_statistics,
                old_airline_code
            )
            background_tasks.add_task(
                service._update_bimo_summary,
                old_airline_code
            )
        
        return updated_review
        
    except HTTPException:
        raise
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{review_id}")
async def delete_review(
    review_id: str,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    리뷰를 삭제합니다.
    
    - **인증 필요**: Bearer Token (본인의 리뷸만 삭제 가능)
    - 리뷰 삭제 시 항공사 통계가 자동으로 업데이트됩니다 (백그라운드에서 처리)
    
    Path Parameters:
    - review_id: 리뷰 ID
    
    Returns:
    - message: 삭제 성공 메시지
    - review_id: 삭제된 리뷰 ID
    """
    try:
        # 토큰 검증
        token = credentials.credentials
        payload = decode_access_token(token)  # 우리 서비스 JWT 디코딩
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        
        # 삭제 전 리뷰 정보 조회 (항공사 코드 확인용)
        old_review = await service.get_review_by_id(review_id)
        airline_code = old_review.airlineCode
        
        # 리뷰 삭제
        result = await service.delete_review(review_id, user_id)
        
        # 백그라운드에서 통계 업데이트
        background_tasks.add_task(
            service._update_airline_statistics,
            airline_code
        )
        # 백그라운드에서 BIMO 요약 업데이트
        background_tasks.add_task(
            service._update_bimo_summary,
            airline_code
        )
        
        return result
    except HTTPException:
        raise
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}/reviews", response_model=reviews_schemas.MyReviewsResponse)
async def get_my_reviews(
    user_id: str,
    limit: int = Query(20, ge=1, le=100, description="조회할 리뷰 개수"),
    offset: int = Query(0, ge=0, description="오프셋 (페이지네이션)"),
    sort: str = Query("latest", description="정렬 옵션: latest, rating_high, rating_low"),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    사용자가 작성한 리뷰 목록을 조회합니다 (총 개수 포함).
    
    ### Path Parameters
    - **user_id**: 사용자 ID
    
    ### Query Parameters
    - **limit**: 조회할 리뷰 개수 (기본값: 20, 최대: 100)
    - **offset**: 오프셋 (페이지네이션, 기본값: 0)
    - **sort**: 정렬 옵션
      - `latest`: 최신순 (기본값)
      - `rating_high`: 평점 높은 순
      - `rating_low`: 평점 낮은 순
    
    ### Returns
    ```json
    {
      "user_id": "kMnkTjxuKRy8QWjBzt8xRk6kGG2",
      "total_count": 15,
      "reviews": [...],
      "has_more": true
    }
    ```
    
    ### Example
    ```
    GET /reviews/users/{user_id}/reviews?limit=20&sort=latest
    ```
    """
    try:
        # 사용자 리뷰 조회 (total_count, has_more 포함)
        response = await service.get_reviews_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            sort=sort
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")


@router.post("/{review_id}/like")
async def add_like_to_review(
    review_id: str,
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    리뷰에 좋아요를 추가합니다 (좋아요 수 +1).
    
    ### Path Parameters
    - **review_id**: 리뷰 ID
    
    ### Returns
    ```json
    {
      "review_id": "abc123",
      "likes": 15,
      "message": "좋아요가 추가되었습니다."
    }
    ```
    
    ### Example
    ```
    POST /reviews/{review_id}/like
    ```
    """
    try:
        result = await service.increment_likes(review_id)
        
        return {
            "review_id": result["review_id"],
            "likes": result["likes"],
            "message": "좋아요가 추가되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")



