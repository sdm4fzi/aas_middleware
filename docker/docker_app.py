from aas_middleware import Middleware
from aas_middleware.model.formatting.aas.aas_model import AAS


middleware = Middleware()
middleware.generate_model_registry_api()
app = middleware.app