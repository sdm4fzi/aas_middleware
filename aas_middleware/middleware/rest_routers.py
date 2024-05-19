from __future__ import annotations

from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

from typing import TYPE_CHECKING, List, Type, Dict

from aas_middleware.connect.consumers.consumer import Consumer
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
    for field_info in aas.model_fields.values():
        if field_info.annotation == submodel:
            if field_info.is_required():
                return False
            else:
                return True
    raise ValueError(
        f"Submodel {submodel.__name__} is not a submodel of {aas.__name__}."
    )


class RestRouter:
    def __init__(self, data_model: DataModel, data_model_name: str, middleware: Middleware):
        self.data_model = data_model
        self.data_model_name = data_model_name
        self.aas_data_model = DataModelRebuilder(data_model=data_model).rebuild_data_model_for_AAS_structure()

        self.middleware = middleware

    def get_provider(self, item_id: str) -> Provider[AAS | Submodel]:
        return self.middleware.get_persistence_provider(self.data_model_name, item_id)
    
    def get_consumer(self, item_id: str) -> Consumer[AAS | Submodel]:
        return self.middleware.get_persistence_consumer(self.data_model_name, item_id)
    
    def generate_submodel_endpoints_from_model(
            self,
        aas_model_type: Type[AAS], submodel_model_type: Type[Submodel],
    ) -> APIRouter:
        """
        Generates CRUD endpoints for a submodel of a pydantic model representing an aas.

        Args:
            aas_model_type (Type[BaseModel]): Pydantic model representing the aas of the submodel.
            submodel_model_type (Type[base.Submodel]): Pydantic model representing the submodel.

        Returns:
            APIRouter: FastAPI router with CRUD endpoints for the given submodel that performs Middleware syxnchronization.
        """
        model_name = aas_model_type.__name__
        submodel_name = submodel_model_type.__name__
        optional_submodel = check_if_submodel_is_optional_in_aas(aas_model_type, submodel_model_type)
        # TODO: the data model name should be used for creating the endpoint
        router = APIRouter(
            prefix=f"/{model_name}/{{item_id}}/{submodel_name}",
            tags=[model_name],
            responses={404: {"description": "Not found"}},
        )

        @router.get(
            "/",
            response_model=submodel_model_type,
        )
        async def get_item(item_id: str):
            # TODO: item_id represents the aas_id of the submodel -> execute provider of aas and retrieve only submodel field from it.
            return await self.get_provider(item_id).execute()

        if optional_submodel:

            @router.post("/")
            async def post_item(item_id: str, item: submodel_model_type) -> Dict[str, str]:
                await self.get_consumer(item.id).execute(item)
                # TODO: also update the submodel in the aas containing the submodel
                return {
                    "message": f"Succesfully created submodel {submodel_name} of aas with id {item_id}"
                }

        @router.put("/")
        async def put_item(item_id: str, item: submodel_model_type) -> Dict[str, str]:
            await self.get_consumer(item_id).execute(item)
            # TODO: also update the submodel in the aas containing the submodel
            # TODO: also update the item_id in the consumer if the new item has another id.
            return {
                "message": f"Succesfully updated submodel {submodel_name} of aas with id {item_id}"
            }

        if optional_submodel:

            @router.delete("/")
            async def delete_item(item_id: str):
                # TODO: add functionality that an empty execute bdoy is a delete
                await self.get_consumer(item_id).execute()
                # TODO: also update the submodel in the aas containing the submodel
                return {
                    "message": f"Succesfully deleted submodel {submodel_name} of aas with id {item_id}"
                }

        return router


    def generate_aas_endpoints_from_model(self, aas_model_type: Type[AAS]) -> APIRouter:
        """
        Generates CRUD endpoints for a pydantic model representing an aas.

        Args:
            aas_model_type (Type[AAS]): Pydantic model representing an aas

        Returns:
            APIRouter: FastAPI router with CRUD endpoints for the given pydantic model that performs Middleware syxnchronization.
        """
        router = APIRouter(
            prefix=f"/{aas_model_type.__name__}",
            tags=[aas_model_type.__name__],
            responses={404: {"description": "Not found"}},
        )

        @router.get("/", response_model=List[aas_model_type])
        async def get_items():
            aas_list = []
            all_model_ids = [model.id for model in self.data_model.get_models_of_type(aas_model_type)]
            for model_id in all_model_ids:
                retrieved_aas = await self.get_provider(model_id).execute()
                aas_list.append(retrieved_aas)
            return aas_list

        @router.post(f"/")
        async def post_item(item: aas_model_type) -> Dict[str, str]:
            await self.get_consumer(item.id).execute(item)
            return {
                "message": f"Succesfully created aas {aas_model_type.__name__} with id {item.id}"
            }

        @router.get("/{item_id}", response_model=aas_model_type)
        async def get_item(item_id: str):
            return await self.get_provider(item_id).execute()

        @router.put("/{item_id}")
        async def put_item(item_id: str, item: aas_model_type) -> Dict[str, str]:
            await self.get_consumer(item_id).execute(item)
            # TODO: also update the item_id in the consumer if the new item has another id.
            return {"message": f"Succesfully updated aas with id {item.id}"}

        @router.delete("/{item_id}")
        async def delete_item(item_id: str):
            await self.get_consumer(item_id).execute()
            # TODO: implement logic in consumers, that if nothing is send, a delete method is performed.
            return {"message": f"Succesfully deleted aas with id {item_id}"}

        return router

    
    
    def generate_endpoints_from_model(self, pydantic_model: Type[BaseModel], middleware: Middleware) -> List[APIRouter]:
        """
        Generates CRUD endpoints for a pydantic model representing an aas and its submodels.

        Args:
            pydantic_model (Type[BaseModel]): Pydantic model representing an aas with submodels.

        Returns:
            List[APIRouter]: List of FastAPI routers with CRUD endpoints for the given pydantic model and its submodels that perform Middleware syxnchronization.
        """
        routers = []
        routers.append(self.generate_aas_endpoints_from_model(pydantic_model))
        submodels = get_all_submodels_from_model(pydantic_model)
        for submodel in submodels:
            routers.append(self.generate_submodel_endpoints_from_model(pydantic_model, submodel))
        return routers
    

    def generate_endpoints(self) -> List[APIRouter]:
        """
        Generates CRUD endpoints for a pydantic model representing an aas and its submodels.

        Returns:
            List[APIRouter]: List of FastAPI routers with CRUD endpoints for the given pydantic model and its submodels that perform Middleware syxnchronization.
        """
        routers = []

        for top_level_model_type in self.aas_data_model.get_top_level_types():
            routers += self.generate_endpoints_from_model(top_level_model_type)
        return routers