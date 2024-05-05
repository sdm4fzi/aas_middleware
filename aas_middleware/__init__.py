from aas_middleware.middleware.middleware import Middleware
from importlib_metadata import version

def get_version(package_name: str) -> str:
    return version(package_name)

# usage
VERSION = get_version("aas_middleware")