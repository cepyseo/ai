from quart import Quart
from hypercorn.config import Config
from config.settings import PORT

app = Quart(__name__)

def create_app():
    config = Config()
    config.bind = [f"0.0.0.0:{PORT}"]
    config.keep_alive_timeout = 300
    config.graceful_timeout = 300
    config.worker_class = "asyncio"
    config.workers = 1
    config.timeout_keep_alive = 300
    config.timeout_graceful_shutdown = 300
    config.backlog = 100
    config.use_reloader = False
    
    return app, config 