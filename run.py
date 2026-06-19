from fastapi import FastAPI
from pathlib import Path
from sdx_base.run import initialise
from sdx_base.server.server import RouterConfig
from sdx_base.server.servers import default_server
from sdx_base.server.tx_id import txid_not_applicable

from app.middleware.timing import TimingMiddleware
from app.routes import router
from app.settings import Settings, ROOT, get_instance

# Description for the OpenAPI documentation, which will be displayed in the API docs /docs or /redoc
description = """

## Documentation

 TODO - put link to documentation

"""


def load_startup_banner() -> str:
    """
    Load the ascii banner
    """
    banner_path = Path(ROOT) / "banner.txt"
    try:
        return banner_path.read_text()
    except (OSError, UnicodeDecodeError):
        return "sds-loader"


# Basic router configuration
router_1 = RouterConfig(router, tx_id_getter=txid_not_applicable)

# Initialize the FastAPI app with the specified settings, routers, and project root.
app: FastAPI = initialise(settings=Settings, routers=[router_1], middleware=[TimingMiddleware], proj_root=ROOT)

# Fetch the populated settings
settings = get_instance()


# Add the description to the OpenAPI schema for better documentation.
app.description = description

if __name__ == "__main__":
    print(load_startup_banner())

    default_server(app, port=settings.port)
