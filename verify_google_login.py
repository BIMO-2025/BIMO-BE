
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.feature.auth.providers.google_provider import GoogleAuthProvider
from app.core.exceptions.exceptions import InvalidTokenError

async def test_fallback_verification():
    print("Testing GoogleAuthProvider fallback verification...")

    # Mock token
    mock_token = "mock_ios_token"
    mock_client_id = "129141636882-7iu0m24usb4dvimetr0q7fir7lmi05d9.apps.googleusercontent.com"

    # Mock Firebase verification to fail (simulate iOS token rejection)
    with patch("app.feature.auth.providers.firebase_provider.FirebaseAuthProvider.verify_token") as mock_firebase_verify:
        mock_firebase_verify.side_effect = InvalidTokenError("Firebase audience mismatch")

        # Mock google.oauth2.id_token.verify_oauth2_token to succeed
        with patch("google.oauth2.id_token.verify_oauth2_token") as mock_google_verify:
            mock_google_verify.return_value = {
                "sub": "1234567890",
                "email": "test@example.com",
                "name": "Test User",
                "picture": "http://example.com/pic.jpg",
                "aud": mock_client_id
            }

            # Run verify_token
            try:
                result = await GoogleAuthProvider.verify_token(mock_token)
                print("✅ Verify Token Result:", result)
                
                assert result["uid"] == "1234567890"
                assert result["email"] == "test@example.com"
                assert result["firebase"]["sign_in_provider"] == "google.com"
                print("✅ Fallback verification successful!")

            except Exception as e:
                print(f"❌ Verification failed: {e}")
                raise e

if __name__ == "__main__":
    asyncio.run(test_fallback_verification())
