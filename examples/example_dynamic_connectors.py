import json
import typing
from fastapi import HTTPException
import uvicorn
import aas_middleware
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxTemplateFormatter

middleware = aas_middleware.Middleware()

class TrivialConnector:
    def __init__(self, return_value: str = "default value"):
        self.return_value = return_value

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, body: str) -> None:
        print(body)
        pass

    async def provide(self) -> str:
        return self.return_value


example_connector = TrivialConnector()
middleware.add_connector("test_connector", example_connector, model_type=str)


@middleware.workflow()
def add_dynamic_connectors_workflow(connector_name: str, return_value: str) -> dict[str, str]:
    dynamic_connector = TrivialConnector(return_value=return_value)
    if connector_name in middleware.connection_registry.connectors:
        raise HTTPException(400, "Already exists")
    middleware.add_connector(connector_name, dynamic_connector, model_type=str)
    # force FastAPI to rebuild its OpenAPI schema so `/docs` sees it:
    middleware.app.openapi_schema = None
    return {
        "connector_name": connector_name,
        "return_value": return_value,
        "result": "dynamic connector added",
    }

# test with:
# curl -X 'POST' \
#   'http://127.0.0.1:8000/workflows/add_dynamic_connectors_workflow/execute' \
#   -H 'accept: application/json' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "connector_name": "new_connector",
#   "return_value": "new return value"
# }'

if __name__ == "__main__":
    # uvicorn.run("minimal_example:middleware.app", reload=True)
    uvicorn.run(middleware.app)



