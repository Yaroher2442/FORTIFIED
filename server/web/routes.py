from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError
from sanic import Request
from sanic.views import HTTPMethodView
from sanic.response import json
from loguru import logger
from server.database.models import *
from server.web.auth import Auth, protect
from server.web.dtos import *
from sanic.exceptions import BadRequest

from server.web.utils import encrypt_password

GenericDto = TypeVar('GenericDto', bound=BaseModel)


def validate_dto(r: Request, dto: Type[GenericDto]) -> GenericDto:
    try:
        return dto(**r.json)
    except ValidationError as e:
        raise BadRequest(message="Passed body not correct")


class AppRoute(HTTPMethodView):
    route: str


class RegRoute(AppRoute):
    route = "/user/auth/reg"

    async def post(self, r: Request):
        d = validate_dto(r, UserD.RegDto)
        pswd, salt = encrypt_password(d.password)
        user = await User.create(
            email=d.email,
            password=pswd,
            salt=salt
        )
        return json(await user.values_dict())


class AuthRoute(AppRoute):
    route = "/user/auth"

    async def post(self, r: Request):
        d = validate_dto(r, UserD.Auth)
        auth: Auth = r.app.ctx.auth
        user = await auth.get_user_to_auth(d.email)
        return json(await auth.generate_token(user))


class RefreshTokenRoute(AppRoute):
    route = "/user/auth/refresh"

    @protect()
    async def post(self, r: Request, user: User):
        d = validate_dto(r, UserD.PassRefreshToken)
        auth: Auth = r.app.ctx.auth
        return json(await auth.refresh_token(user, d.refresh_token))
