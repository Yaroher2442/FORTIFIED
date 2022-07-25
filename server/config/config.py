from pydantic import BaseModel


class DbConfig(BaseModel):
    db_url: str


class ServerConfig(BaseModel):
    host: str
    port: int
    database: DbConfig


class TgBotConfig(BaseModel):
    token: str


class GitlabConfig(BaseModel):
    secret_token: str


class AppConfig(BaseModel):
    bot: TgBotConfig

    server: ServerConfig
    gitlab: GitlabConfig
