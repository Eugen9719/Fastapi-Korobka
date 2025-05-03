import jwt
import datetime
import logging
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.interface.repositories.i_user_repo import IUserRepository
from backend.app.models.auth import Token
from backend.app.models.users import UserOauthCreate
from backend.app.services.decorators import HttpExceptionWrapper
from backend.core import security
from backend.core.oauth_config import oauth


logger = logging.getLogger(__name__)
class GoogleAuthService:
    """Сервис аутентификации через Google"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository



    @HttpExceptionWrapper
    async def authenticate(self, request: dict, db: AsyncSession) -> Token:
        token = await self._get_google_token(request)
        id_token = self._extract_id_token(token)
        user_info = self._decode_id_token(id_token)
        user = await self._get_or_create_user(user_info, db)
        return Token(
            access_token=security.create_access_token(user.id),
            refresh_token=security.create_refresh_token(user.id),
            token_type="bearer"
        )

    async def _get_google_token(self, request: dict) -> dict:
            token = await oauth.google.authorize_access_token(request)
            logger.debug(f"Response from Google: {token}")
            return token


    def _extract_id_token(self, token: dict) -> str:
        id_token = token.get('id_token')
        if not id_token:
            logger.error("Missing id_token in Google response")
            raise HTTPException(status_code=400, detail="OAuth error: 'id_token' not found")
        return id_token

    def _decode_id_token(self, id_token: str) -> dict:
            jwks_client = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs")
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)
            user_info = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=oauth.google.client_id,
                issuer="https://accounts.google.com",
                options={"verify_aud": True, "verify_iss": True, "verify_signature": True},
                leeway=datetime.timedelta(seconds=10)
            )
            logger.debug(f"Decoded user info: {user_info}")
            return user_info

    async def _get_or_create_user(self, user_info: dict, db: AsyncSession,):
        email = user_info.get("email")
        if not email:
            logger.error("Email not found in id_token")
            raise HTTPException(status_code=400, detail="Email not found in id_token")

        user = await self.user_repository.get_by_email(db=db, email=email)
        if not user:
            schema = UserOauthCreate(
                email=email,
                first_name=user_info.get("given_name", ""),
                last_name=user_info.get("family_name", ""),
                is_active = True,

            )
            user = await self.user_repository.create(db=db, schema=schema)
        return user
