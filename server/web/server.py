from sanic import Sanic

from server.config.config import ServerConfig
from server.web.auth import Auth
from server.web.routes import AppRoute
from server.database.connection import init


class Server:

    def __init__(self, config: ServerConfig):
        self.config = config
        self.sanic_app = Sanic("App")
        "http://5.35.30.9:8888/"
        self.set_env()

    def set_env(self):
        self.sanic_app.config.TOKEN_LIFETIME = 99999999
        self.sanic_app.config.SECRET = "APP_SECRET"

    async def _before_start(self, app: Sanic, loop):
        await init(self.config.database)
        app.ctx.auth = Auth(self.sanic_app.config.SECRET,
                            self.sanic_app.config.TOKEN_LIFETIME)

    def _configure(self):
        self.sanic_app.before_server_start(self._before_start)
        for view in AppRoute.__subclasses__():
            self.sanic_app.add_route(view.as_view(), view.route)

    def run(self):
        self._configure()
        self.sanic_app.run(self.config.host, self.config.port)
