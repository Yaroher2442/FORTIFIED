import json

from config.config import AppConfig
from server.web.log_ext import LogsHandlerExt
from server.web.server import Server


class App:
    def __init__(self, config: AppConfig):
        self.server = Server(config.server)

    def run(self):
        LogsHandlerExt.set_logger()
        self.server.run()
        # asyncio.run(self.bot.run())


if __name__ == '__main__':
    conf = json.loads(open("config/config.json", "r").read())
    app = App(AppConfig(**conf))
    app.run()
