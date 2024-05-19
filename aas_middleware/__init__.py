from aas_middleware.middleware.middleware import Middleware
import toml
import importlib_metadata
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_version() -> str:
    try:
        return importlib_metadata.version("aas_middleware")
    except:
        logger.info("Could not find version in package metadata. Trying to read from pyproject.toml")
    try:
        pyproject = toml.load("pyproject.toml")
        return pyproject["tool"]["poetry"]["version"]
    except:
        logger.error("Could not find pyproject.toml file. Trying to read from poetry.lock")
    raise ModuleNotFoundError("Could not find version in package metadata or pyproject.toml")

VERSION = get_version()
