from aas_middleware import Middleware
from aas_pydantic.aas_model import AAS


middleware = Middleware()
middleware.generate_model_registry_api()
app = middleware.app
