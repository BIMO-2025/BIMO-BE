"""
알림 서비스 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.feature.notifications.notification_service import (
    get_user_fcm_tokens,
    update_user_fcm_token,
    remove_user_fcm_token,
    send_notification_to_user_by_uid
)
from app.core.exceptions.exceptions import DatabaseError


@pytest.mark.asyncio
class TestGetUserFcmTokens:
    """FCM 토큰 조회 테스트"""

    async def test_get_fcm_tokens_success(self):
        """FCM 토큰 조회 성공"""
        # Arrange
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "fcm_tokens": ["token1", "token2", "token3"]
        }
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            # Act
            tokens = await get_user_fcm_tokens("test_user_id")
            
            # Assert
            assert len(tokens) == 3
            assert "token1" in tokens
            assert "token2" in tokens
            assert "token3" in tokens

    async def test_get_fcm_tokens_user_not_found(self):
        """사용자를 찾을 수 없는 경우"""
        mock_doc = MagicMock()
        mock_doc.exists = False
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            tokens = await get_user_fcm_tokens("invalid_user")
            assert tokens == []

    async def test_get_fcm_tokens_no_tokens(self):
        """FCM 토큰이 없는 경우"""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {}
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            tokens = await get_user_fcm_tokens("test_user_id")
            assert tokens == []

    async def test_get_fcm_tokens_database_error(self):
        """데이터베이스 오류인 경우"""
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.side_effect = Exception("DB Connection Error")
            
            with pytest.raises(DatabaseError) as exc_info:
                await get_user_fcm_tokens("test_user_id")
            
            assert "FCM 토큰 조회 중오류 발생" in str(exc_info.value.message)


@pytest.mark.asyncio
class TestUpdateUserFcmToken:
    """FCM 토큰 업데이트 테스트"""

    async def test_update_fcm_token_add_new(self):
        """새 FCM 토큰 추가"""
        # Arrange
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "fcm_tokens": ["existing_token"]
        }
        mock_ref = MagicMock()
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            # 첫 번째 호출은 get, 두 번째는 update
            mock_thread.side_effect = [mock_doc, None]
            
            with patch("app.feature.notifications.notification_service.user_collection.document") as mock_doc_ref:
                mock_doc_ref.return_value = mock_ref
                
                # Act
                result = await update_user_fcm_token("test_user_id", "new_token")
                
                # Assert
                assert result is True

    async def test_update_fcm_token_duplicate(self):
        """중복 FCM 토큰은 추가하지 않음"""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "fcm_tokens": ["existing_token"]
        }
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            result = await update_user_fcm_token("test_user_id", "existing_token")
            assert result is True

    async def test_update_fcm_token_user_not_found(self):
        """사용자를 찾을 수 없는 경우"""
        mock_doc = MagicMock()
        mock_doc.exists = False
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            result = await update_user_fcm_token("invalid_user", "new_token")
            assert result is False

    async def test_update_fcm_token_database_error(self):
        """데이터베이스 오류 처리"""
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.side_effect = Exception("DB Connection Error")
            
            with pytest.raises(DatabaseError) as exc_info:
                await update_user_fcm_token("test_user_id", "new_token")
            
            assert "FCM 토큰 업데이트 중 오류 발생" in str(exc_info.value.message)


@pytest.mark.asyncio
class TestRemoveUserFcmToken:
    """FCM 토큰 제거 테스트"""

    async def test_remove_fcm_token_success(self):
        """FCM 토큰 제거 성공"""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "fcm_tokens": ["token1", "token2"]
        }
        mock_ref = MagicMock()
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.side_effect = [mock_doc, None]
            
            with patch("app.feature.notifications.notification_service.user_collection.document") as mock_doc_ref:
                mock_doc_ref.return_value = mock_ref
                
                result = await remove_user_fcm_token("test_user_id", "token1")
                assert result is True

    async def test_remove_fcm_token_not_exists(self):
        """존재하지 않는 토큰 제거 시도"""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "fcm_tokens": ["token1"]
        }
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            result = await remove_user_fcm_token("test_user_id", "non_existent_token")
            assert result is True

    async def test_remove_fcm_token_user_not_found(self):
        """사용자를 찾을 수 없는 경우"""
        mock_doc = MagicMock()
        mock_doc.exists = False
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            result = await remove_user_fcm_token("invalid_user", "token1")
            assert result is False


@pytest.mark.asyncio
class TestSendNotificationToUserByUid:
    """UID로 알림 전송 테스트"""

    async def test_send_notification_success(self):
        """알림 전송 성공"""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "fcm_tokens": ["token1", "token2"]
        }
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            with patch("app.feature.notifications.notification_service.send_notification_to_user") as mock_send:
                mock_send.return_value = {"success": True}
                
                result = await send_notification_to_user_by_uid(
                    uid="test_user_id",
                    title="테스트 제목",
                    body="테스트 본문"
                )
                
                assert result["success"] is True
                mock_send.assert_called_once()

    async def test_send_notification_with_data_and_image(self):
        """데이터와 이미지를 포함한 알림 전송"""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "fcm_tokens": ["token1"]
        }
        
        with patch("app.feature.notifications.notification_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            with patch("app.feature.notifications.notification_service.send_notification_to_user") as mock_send:
                mock_send.return_value = {"success": True}
                
                result = await send_notification_to_user_by_uid(
                    uid="test_user_id",
                    title="제목",
                    body="본문",
                    data={"key": "value"},
                    image_url="https://example.com/image.png"
                )
                
                assert result["success"] is True
                # data와 image_url이 전달되었는지 확인
                call_args = mock_send.call_args
                assert call_args[1]["data"] == {"key": "value"}
                assert call_args[1]["image_url"] == "https://example.com/image.png"
