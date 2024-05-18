from __future__ import annotations

from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

from typing import TYPE_CHECKING, List, Type, Dict

from aas_middleware.connect.consumers.consumers import Consumer
from aas_middleware.connect.providers.provider import Provider
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder
from aas_middleware.model.formatting.aas.aas_middleware_util import get_all_submodels_from_model
from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel

if TYPE_CHECKING:
    from aas_middleware.middleware.middleware import Middleware

def check_if_submodel_is_optional_in_aas(
    aas: Type[AAS], submodel: Type[Submodel]
) -> bool:
    """
    Checks if a submodel is an optional attribute in an aas.

    Args:
        aas (Type[base.AAS]): AAS model.
        submodel (Type[base.Submodel]): Submodel to be checked.

    Raises:
        ValueError: If the submodel is not a submodel of the aas.

    Returns:
        bool: True if the submodel is an optional attribute in the aas, False otherwise.
    """
    for field_name, field_info in aas.model_fields.items():
        if field_info.annotation == submodel:
            if field_info.is_required():
                return False
            else:
                return True
    raise ValueError(
        f"Submodel {submodel.__name__} is not a submodel of {aas.__name__}."
    )


def generate_submodel_endpoints_from_model(
    # TODO: inject here the middleware to access the persistence providers and consumers to retrieve the data from the objects by using BasyxConnectors
    pydantic_model: Type[AAS], submodel: Type[Submodel],
    providers: List[Provider[Submodel]], consumers: List[Consumer[Submodel]]
) -> APIRouter:
    """
    Generates CRUD endpoints for a submodel of a pydantic model representing an aas.

    Args:
        pydantic_model (Type[BaseModel]): Pydantic model representing the aas of the submodel.
        submodel (Type[base.Submodel]): Pydantic model representing the submodel.

    Returns:
        APIRouter: FastAPI router with CRUD endpoints for the given submodel that performs Middleware syxnchronization.
    """
    model_name = pydantic_model.__name__
    submodel_name = submodel.__name__
    optional_submodel = check_if_submodel_is_optional_in_aas(pydantic_model, submodel)
    router = APIRouter(
        prefix=f"/{model_name}/{{item_id}}/{submodel_name}",
        tags=[model_name],
        responses={404: {"description": "Not found"}},
    )

    @router.get(
        "/",
        response_model=submodel,
    )
    async def get_item(item_id: str):
        # TODO: use hash tables in a class RestRouter to realize this behavior
        for provider in providers:
            if provider.item_id == item_id:
                return await provider.execute()

    if optional_submodel:

        @router.post("/")
        async def post_item(item_id: str, item: submodel) -> Dict[str, str]:
            for consumer in consumers:
                if consumer.item_id == item.id:
                    await consumer.execute(item)
                    return {
                        "message": f"Succesfully created submodel {submodel_name} of aas with id {item_id}"
                    }

    @router.put("/")
    async def put_item(item_id: str, item: submodel) -> Dict[str, str]:
        for consumer in consumers:
                if consumer.item_id == item_id:
                    # TODO: also update the item_id in the consumer if the new item has another id.
                    await consumer.execute(item)
                    return {
                        "message": f"Succesfully updated submodel {submodel_name} of aas with id {item_id}"
                    }

    if optional_submodel:

        @router.delete("/")
        async def delete_item(item_id: str):
            for consumer in consumers:
                if consumer.item_id == item_id:
                    # TODO: implement logic in consumers, that if nothing is send, a delete method is performed.
                    await consumer.execute()
                    return {
                        "message": f"Succesfully deleted submodel {submodel_name} of aas with id {item_id}"
                    }

    return router


def generate_aas_endpoints_from_model(pydantic_model: Type[AAS], providers: List[Provider[AAS]], consumers: List[Consumer[AAS]]) -> APIRouter:
    """
    Generates CRUD endpoints for a pydantic model representing an aas.

    Args:
        pydantic_model (Type[BaseModel]): Pydantic model representing an aas

    Returns:
        APIRouter: FastAPI router with CRUD endpoints for the given pydantic model that performs Middleware syxnchronization.
    """
    router = APIRouter(
        prefix=f"/{pydantic_model.__name__}",
        tags=[pydantic_model.__name__],
        responses={404: {"description": "Not found"}},
    )

    @router.get("/", response_model=List[pydantic_model])
    async def get_items():
        aas_list = []
        for provider in providers:
            retrieved_aas = await provider.execute()
            aas_list.append(retrieved_aas)
        return aas_list

    @router.post(f"/")
    async def post_item(item: pydantic_model) -> Dict[str, str]:
        for consumer in consumers:
                if consumer.item_id == item.id:
                    await consumer.execute(item)
                    return {
                        "message": f"Succesfully created aas {pydantic_model.__name__} with id {item.id}"
                    }

    @router.get("/{item_id}", response_model=pydantic_model)
    async def get_item(item_id: str):
        for provider in providers:
            if provider.item_id == item_id:
                return await provider.execute()

    @router.put("/{item_id}")
    async def put_item(item_id: str, item: pydantic_model) -> Dict[str, str]:
        for consumer in consumers:
                # TODO: also update the item_id in the consumer if the new item has another id.
                if consumer.item_id == item.id:
                    await consumer.execute(item)
                    return {"message": f"Succesfully updated aas with id {item.id}"}

    @router.delete("/{item_id}")
    async def delete_item(item_id: str):
        for consumer in consumers:
            if consumer.item_id == item_id:
                # TODO: implement logic in consumers, that if nothing is send, a delete method is performed.
                await consumer.execute()
                return {"message": f"Succesfully deleted aas with id {item_id}"}

    return router


def generate_endpoints_from_model(pydantic_model: Type[BaseModel], middleware: Middleware) -> List[APIRouter]:
    """
    Generates CRUD endpoints for a pydantic model representing an aas and its submodels.

    Args:
        pydantic_model (Type[BaseModel]): Pydantic model representing an aas with submodels.

    Returns:
        List[APIRouter]: List of FastAPI routers with CRUD endpoints for the given pydantic model and its submodels that perform Middleware syxnchronization.
    """
    routers = []
    # instead of injecting the middleware here -> create a rest router class that
    # retrieves from the middleware these objects
    providers = middleware.get_persistence_providers_for_type(pydantic_model)
    consumers = middleware.get_persistence_consumers_for_type(pydantic_model)
    routers.append(generate_aas_endpoints_from_model(pydantic_model, providers, consumers))
    submodels = get_all_submodels_from_model(pydantic_model)
    for submodel in submodels:
        providers = middleware.get_persistence_providers_for_type(submodel)
        consumers = middleware.get_persistence_consumers_for_type(submodel)
        routers.append(generate_submodel_endpoints_from_model(pydantic_model, submodel, providers, consumers))

    return routers

def generate_endpoints_from_data_model(data_model: DataModel, middleware: Middleware) -> List[APIRouter]:
    """
    Generates CRUD endpoints for a pydantic model representing an aas and its submodels.

    Args:
        pydantic_model (Type[BaseModel]): Pydantic model representing an aas with submodels.

    Returns:
        List[APIRouter]: List of FastAPI routers with CRUD endpoints for the given pydantic model and its submodels that perform Middleware syxnchronization.
    """
    rebuild_data_model = DataModelRebuilder(data_model=data_model).rebuild_data_model_for_AAS_structure()
    routers = []

    for top_level_model_type in rebuild_data_model.get_top_level_types():
        routers += generate_endpoints_from_model(top_level_model_type, middleware)

    return routers
