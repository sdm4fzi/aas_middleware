from typing import Type
from aiohttp import streamer
import fastapi
from pydantic import BaseModel, ConfigDict, create_model

class FrozenModel(BaseModel):
    id: int
    name: str



app = fastapi.FastAPI()


def create_post_endpoint(model_type: Type[FrozenModel]):
    @app.post("/model")
    async def create_model(model: model_type) -> FrozenModel:
        return model

# create_post_endpoint(FrozenModel)

dynamic_created_model = create_model("DynamicModel", id=(int, ...), name2=(str, ...))
create_post_endpoint(dynamic_created_model)

import uvicorn
uvicorn.run(app)