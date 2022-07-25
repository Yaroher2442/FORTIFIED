import time
from functools import wraps
from typing import Dict

import jwt
from pydantic import EmailStr
from sanic import Request
from sanic.exceptions import Forbidden, InvalidHeader, NotFound
from tortoise.transactions import atomic

from server.database.models import User, UserTokens


class Auth:
    def __init__(self, _secret: str, token_live_time: int):
        self._secret = _secret
        self._token_live_time = token_live_time

    @atomic()
    async def generate_token(self, user: User) -> Dict:
        expire_at = int(time.time() + self._token_live_time)
        access_token = jwt.encode({"user_id": user.id, "expire_at": expire_at}, self._secret)
        refresh_token = jwt.encode({"user_id": user.id, "access_token": access_token}, self._secret)
        await UserTokens.create(user=user,
                                access_token=access_token,
                                refresh_token=refresh_token,
                                expire_at=expire_at)
        return {"access_token": access_token, "refresh_token": refresh_token,
                "expire_timestamp": expire_at}

    @atomic()
    async def refresh_token(self, user: User, refresh_token: str) -> Dict:
        try:
            data = jwt.decode(
                refresh_token, self._secret, algorithms=["HS256"]
            )
            access_token = data['access_token']
            user_id = int(data['user_id'])
        except (jwt.exceptions.InvalidTokenError, KeyError, ValueError):
            raise Forbidden(message="Incorrect token")
        if user_id != user.id:
            raise Forbidden(message="Incorrect token")
        tokens = await UserTokens.filter(access_token=access_token, refresh_token=refresh_token).first()
        if not tokens:
            raise Forbidden(message="Incorrect token")
        await tokens.delete()
        return await self.generate_token(user)

    @atomic
    async def get_user_to_auth(self, email: EmailStr):
        user = await User.get_or_none(email=email)
        if not User:
            raise NotFound(message="User with this email not found")
        return user

    @atomic()
    async def validate_request(self, request: Request, pass_not_verified: bool = False, pass_expire=False) -> User:
        if not request.token:
            raise InvalidHeader(message="Token not found")
        try:
            data = jwt.decode(
                request.token, request.app.config.SECRET, algorithms=["HS256"]
            )
            expire_at = int(data['expire_at'])
            user_id = int(data['user_id'])
        except (jwt.exceptions.InvalidTokenError, KeyError, ValueError):
            raise Forbidden(message="Invalid token")
        if expire_at < time.time() and not pass_expire:
            raise Forbidden(message="Token expired")
        tokens: UserTokens = await UserTokens.filter(access_token=request.token,
                                                     user_id=user_id).first().select_related("user")
        if not tokens:  # or tokens.expire_at != expire_at:
            raise Forbidden(message="Invalid token")
        if not pass_not_verified and not tokens.user.verified:
            raise Forbidden(message="Not verified user")
        await tokens.user.save(update_fields=['last_active'])
        return tokens.user


def protect(retrieve_user: bool = True, pass_expire: bool = False):
    def called(method):
        @wraps(method)
        async def f(*args, **kwargs):
            cls = args[0]
            initial_args = args
            request: Request = args[1]

            user = await request.app.ctx.auth.validate_request(request, pass_expire=pass_expire)
            if retrieve_user:
                initial_args += (user,)
            return await method(*initial_args, **kwargs)

        return f

    return called
