import toml
import importlib_metadata
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_version() -> str:
    try:
        return importlib_metadata.version("aas_middleware")
    except:
        logger.info(
            "Could not find version in package metadata. Trying to read from pyproject.toml"
        )
    try:
        pyproject = toml.load("pyproject.toml")
        return pyproject["tool"]["poetry"]["version"]
    except:
        logger.error(
            "Could not find pyproject.toml file. Trying to read from poetry.lock"
        )
    raise ModuleNotFoundError(
        "Could not find version in package metadata or pyproject.toml"
    )


VERSION = get_version()

from aas_middleware.middleware.middleware import Middleware
from aas_middleware.middleware.aas_persistence_middleware import AasMiddleware

from aas_middleware.model.core import Reference, Identifier
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder

from aas_pydantic.aas_model import AAS, Submodel, SubmodelElementCollection, Blob, File

from aas_middleware.model import formatting

from aas_middleware.connect import connectors

# New modules moved from root directory
from aas_middleware.core import (
    bindings, config_model, errors, events, 
    instrumentation, registries
)
from aas_middleware.domain import data_model
from aas_middleware.ports import connector, lifecycle, discovery
from aas_middleware.utils import logging as utils_logging
from aas_middleware.facade import app, builder, rest_api

__all__ = [
    # Existing exports
    "Middleware",
    "AasMiddleware", 
    "Reference",
    "Identifier",
    "DataModel",
    "DataModelRebuilder",
    "AAS",
    "Submodel",
    "SubmodelElementCollection",
    "Blob",
    "File",
    "formatting",
    "connectors",
    "VERSION",
    
    # New exports from moved modules
    "bindings",
    "config_model", 
    "errors",
    "events",
    "instrumentation",
    "registries",
    "data_model",
    "connector",
    "lifecycle",
    "discovery",
    "utils_logging",
    "app",
    "builder",
    "rest_api"
]
