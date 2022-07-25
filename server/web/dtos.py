from pydantic import BaseModel, EmailStr


class UserD:
    class RegDto(BaseModel):
        email: EmailStr
        password: str

    class Auth(BaseModel):
        email: EmailStr
        password: str

    class PassRefreshToken(BaseModel):
        refresh_token: str


class PhotoD:
    class CreateNew(BaseModel):
        dir: int | None
        display_name: str | None
        from_app: str | None
