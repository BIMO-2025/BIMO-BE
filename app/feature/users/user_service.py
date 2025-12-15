"""
사용자 관련 서비스 모듈
"""

from datetime import datetime, timezone
from fastapi.concurrency import run_in_threadpool

from app.feature.auth.providers.base_provider import BaseAuthProvider
from app.core.firebase import db
from app.shared.schemas import UserInDB
from app.core.exceptions.exceptions import (
    DatabaseError,
    UserProfileNotFoundError,
    CustomException,
)

# Firestore 'users' 컬렉션 참조
user_collection = db.collection("users")


class UserService:
    """사용자 관련 비즈니스 로직을 처리하는 서비스"""

    @staticmethod
    async def update_display_name(uid: str, display_name: str) -> UserInDB:
        """
        사용자의 display_name(닉네임)을 업데이트합니다.
        
        Args:
            uid: 사용자 UID
            display_name: 새로운 닉네임
            
        Returns:
            업데이트된 사용자 정보 (UserInDB)
            
        Raises:
            UserProfileNotFoundError: 사용자를 찾을 수 없을 때
            DatabaseError: Firestore 업데이트 실패 시
        """
        # 1. Firestore에서 사용자 조회
        user_ref = user_collection.document(uid)
        user_doc = await run_in_threadpool(user_ref.get)
        
        if not user_doc.exists:
            raise UserProfileNotFoundError(user_id=uid)
        
        # 2. display_name 업데이트
        # 닉네임만 업데이트하므로 last_login_at은 변경하지 않음
        update_data = {
            "display_name": display_name.strip()
        }
        
        try:
            # Firestore 업데이트
            await run_in_threadpool(user_ref.update, update_data)
            
            # 3. 업데이트된 사용자 정보 조회 및 반환
            updated_doc = await run_in_threadpool(user_ref.get)
            user_data = updated_doc.to_dict()
            
            # 필수 필드 확인 및 기본값 설정
            if not user_data:
                raise DatabaseError(message="사용자 데이터를 가져올 수 없습니다.")
            
            # 필수 필드가 없으면 기본값 설정
            if "fcm_tokens" not in user_data:
                user_data["fcm_tokens"] = []
            
            # datetime 필드 정규화
            user_data = BaseAuthProvider._normalize_datetime_fields(user_data)
            
            return UserInDB(**user_data)
            
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"닉네임 업데이트 실패: {e}")

    @staticmethod
    async def update_sleep_pattern(
        uid: str, 
        sleep_start: str, 
        sleep_end: str
    ) -> dict:
        """
        사용자의 수면 패턴을 업데이트합니다.
        
        Args:
            uid: 사용자 UID
            sleep_start: 수면 시작 시간 (HH:MM 형식, 한국 시간 기준)
            sleep_end: 수면 종료 시간 (HH:MM 형식, 한국 시간 기준)
            
        Returns:
            업데이트된 수면 패턴 정보
            
        Raises:
            UserProfileNotFoundError: 사용자를 찾을 수 없을 때
            DatabaseError: Firestore 업데이트 실패 시
        """
        # 1. Firestore에서 사용자 조회
        user_ref = user_collection.document(uid)
        user_doc = await run_in_threadpool(user_ref.get)
        
        if not user_doc.exists:
            raise UserProfileNotFoundError(user_id=uid)
        
        # 2. HH:MM 형식을 datetime으로 변환 (한국 시간 기준)
        from datetime import datetime
        import pytz
        
        try:
            # "23:00" -> datetime(2025, 1, 1, 23, 0, 0)
            start_hour, start_minute = map(int, sleep_start.split(':'))
            end_hour, end_minute = map(int, sleep_end.split(':'))
            
            # 한국 시간대 (KST, UTC+9)
            kst = pytz.timezone('Asia/Seoul')
            
            # 한국 시간으로 저장
            sleep_pattern_start = kst.localize(datetime(2025, 1, 1, start_hour, start_minute, 0))
            sleep_pattern_end = kst.localize(datetime(2025, 1, 1, end_hour, end_minute, 0))
            
        except ValueError as e:
            raise DatabaseError(message=f"잘못된 시간 형식입니다: {e}")
        
        # 3. 수면 패턴 업데이트
        update_data = {
            "sleepPatternStart": sleep_pattern_start,
            "sleepPatternEnd": sleep_pattern_end
        }
        
        try:
            # Firestore 업데이트
            await run_in_threadpool(user_ref.update, update_data)
            
            return {
                "sleepPatternStart": sleep_start,
                "sleepPatternEnd": sleep_end
            }
            
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"수면 패턴 업데이트 실패: {e}")

    @staticmethod
    async def get_sleep_pattern(uid: str) -> dict:
        """
        사용자의 수면 패턴을 조회합니다 (한국 시간 기준).
        
        Args:
            uid: 사용자 UID
            
        Returns:
            수면 패턴 정보 (HH:MM 형식, 한국 시간)
            
        Raises:
            UserProfileNotFoundError: 사용자를 찾을 수 없을 때
        """
        user_ref = user_collection.document(uid)
        user_doc = await run_in_threadpool(user_ref.get)
        
        if not user_doc.exists:
            raise UserProfileNotFoundError(user_id=uid)
        
        user_data = user_doc.to_dict()
        
        # datetime 객체를 한국 시간 기준 HH:MM 형식으로 변환
        import pytz
        kst = pytz.timezone('Asia/Seoul')
        
        result = {}
        
        if "sleepPatternStart" in user_data and user_data["sleepPatternStart"]:
            sleep_start_dt = user_data["sleepPatternStart"]
            # 한국 시간대로 변환
            if sleep_start_dt.tzinfo is None:
                # timezone 정보가 없으면 UTC로 가정하고 KST로 변환
                sleep_start_dt = pytz.utc.localize(sleep_start_dt).astimezone(kst)
            else:
                # 이미 timezone 정보가 있으면 KST로 변환
                sleep_start_dt = sleep_start_dt.astimezone(kst)
            result["sleepPatternStart"] = sleep_start_dt.strftime("%H:%M")
        else:
            result["sleepPatternStart"] = None
        
        if "sleepPatternEnd" in user_data and user_data["sleepPatternEnd"]:
            sleep_end_dt = user_data["sleepPatternEnd"]
            # 한국 시간대로 변환
            if sleep_end_dt.tzinfo is None:
                sleep_end_dt = pytz.utc.localize(sleep_end_dt).astimezone(kst)
            else:
                sleep_end_dt = sleep_end_dt.astimezone(kst)
            result["sleepPatternEnd"] = sleep_end_dt.strftime("%H:%M")
        else:
            result["sleepPatternEnd"] = None
        
        return result

    @staticmethod
    async def get_user_profile(uid: str) -> UserInDB:
        """
        사용자 프로필 정보를 조회합니다.
        
        Args:
            uid: 사용자 UID
            
        Returns:
            사용자 정보 (UserInDB)
            
        Raises:
            UserProfileNotFoundError: 사용자를 찾을 수 없을 때
        """
        user_ref = user_collection.document(uid)
        user_doc = await run_in_threadpool(user_ref.get)
        
        if not user_doc.exists:
            raise UserProfileNotFoundError(user_id=uid)
        
        user_data = user_doc.to_dict()
        
        # 필수 필드 확인 및 기본값 설정
        if "fcm_tokens" not in user_data:
            user_data["fcm_tokens"] = []
            
        # datetime 필드 정규화
        user_data = BaseAuthProvider._normalize_datetime_fields(user_data)
        
        return UserInDB(**user_data)

    @staticmethod
    async def update_photo_url(uid: str, photo_url: str) -> UserInDB:
        """
        사용자의 프로필 사진 URL을 업데이트합니다.
        
        Args:
            uid: 사용자 UID
            photo_url: 새로운 프로필 사진 URL
            
        Returns:
            업데이트된 사용자 정보 (UserInDB)
            
        Raises:
            UserProfileNotFoundError: 사용자를 찾을 수 없을 때
            DatabaseError: Firestore 업데이트 실패 시
        """
        # 1. Firestore에서 사용자 조회
        user_ref = user_collection.document(uid)
        user_doc = await run_in_threadpool(user_ref.get)
        
        if not user_doc.exists:
            raise UserProfileNotFoundError(user_id=uid)
        
        # 2. photo_url 업데이트
        update_data = {
            "photo_url": photo_url.strip()
        }
        
        try:
            # Firestore 업데이트
            await run_in_threadpool(user_ref.update, update_data)
            
            # 3. 업데이트된 사용자 정보 조회 및 반환
            updated_doc = await run_in_threadpool(user_ref.get)
            user_data = updated_doc.to_dict()
            
            # 필수 필드 확인 및 기본값 설정
            if not user_data:
                raise DatabaseError(message="사용자 데이터를 가져올 수 없습니다.")
            
            # 필수 필드가 없으면 기본값 설정
            if "fcm_tokens" not in user_data:
                user_data["fcm_tokens"] = []
            
            # datetime 필드 정규화
            user_data = BaseAuthProvider._normalize_datetime_fields(user_data)
            
            return UserInDB(**user_data)
            
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"프로필 사진 업데이트 실패: {e}")
