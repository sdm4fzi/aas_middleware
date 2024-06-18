import typing
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from typing import TYPE_CHECKING, List, Type, Dict, Union
from aas_middleware.connect.connectors.connector import Connector
from aas_middleware.middleware import middleware
from aas_middleware.middleware.registries import ConnectionInfo
from aas_middleware.model import data_model
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.formatting.aas.aas_middleware_util import get_contained_models_attribute_info
from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel

if TYPE_CHECKING:
    from aas_middleware.middleware.middleware import Middleware

def check_if_attribute_is_optional_in_aas(
    aas: Type[AAS], attribute_name: str
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
    if attribute_name not in aas.model_fields:
        raise ValueError(
            f"Submodel {attribute_name} is not a submodel attribute of {aas.__name__}."
        )
    field_info = aas.model_fields[attribute_name]
    if not field_info.is_required():
        return True
    elif typing.get_origin(field_info.annotation) == Union and type(None) in typing.get_args(field_info.annotation):
        return True
    else:
        return False


class RestRouter:
    def __init__(self, data_model: DataModel, data_model_name: str, middleware: "Middleware"):
        self.data_model = data_model
        self.data_model_name = data_model_name
        self.aas_data_model = data_model

        self.middleware = middleware

    def get_connector(self, item_id: str) -> Connector:
        return self.middleware.persistence_registry.get_connection(ConnectionInfo(data_model_name=self.data_model_name, model_id=item_id))
    
    def generate_endpoints_from_contained_model(
            self,
        aas_model_type: Type[AAS], 
        attribute_name: str,
        submodel_model_type: Type[Submodel],
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
        optional_submodel = check_if_attribute_is_optional_in_aas(aas_model_type, attribute_name)
        # TODO: the data model name should be used for creating the endpoint
        # TODO: adjust that no aas or submodel reference appears in the router -> should work for all models.
        router = APIRouter(
            prefix=f"/{model_name}/{{item_id}}/{attribute_name}",
            tags=[model_name],
            responses={404: {"description": "Not found"}},
        )

        @router.get(
            "/",
            response_model=submodel_model_type,
        )
        async def get_item(item_id: str):
            try:
                model = await self.get_connector(item_id).provide()
                return getattr(model, attribute_name)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Submodel with id {item_id} could not be retrieved. Error: {e}"
                )

        if optional_submodel:
            @router.post("/")
            async def post_item(item_id: str, item: submodel_model_type) -> Dict[str, str]:
                connector = self.get_connector(item_id)
                try: 
                    provided_data = await connector.provide()
                    # TODO: update that the correct type is immediately returned -> using model validate inside the connector
                    provided_data_dict = provided_data.model_dump()
                    model = aas_model_type.model_validate(provided_data_dict)
                    setattr(model, attribute_name, item)
                    await connector.consume(model)
                    return {
                        "message": f"Succesfully created attribute {attribute_name} of aas with id {item_id}"
                    }
                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Attribute {attribute_name} for model with id {item_id} could not be set. Error: {e}"
                    )

        @router.put("/")
        async def put_item(item_id: str, item: submodel_model_type) -> Dict[str, str]:
            connector = self.get_connector(item_id)
            try:
                model = await connector.provide()
                if getattr(model, attribute_name) == item:
                    return {
                        "message": f"Attribute {attribute_name} of model with id {item_id} is already up to date"
                    }
                setattr(model, attribute_name, item)
                await connector.consume(model)
                return {
                    "message": f"Succesfully updated attribute {attribute_name} of model with id {item_id}"
                }
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Attribute {attribute_name} of model with id {item_id} could not be updated. Error: {e}"
                )

        if optional_submodel:

            @router.delete("/")
            async def delete_item(item_id: str):
                connector = self.get_connector(item_id)
                try:
                    model = await connector.provide()
                    setattr(model, attribute_name, None)
                    await connector.consume(model)
                    return {
                        "message": f"Succesfully deleted attribute {attribute_name} of model with id {item_id}"
                    }
                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"attribute {attribute_name} of model with id {item_id} could not be deleted. Error: {e}"
                    )

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
            connection_infos = self.middleware.persistence_registry.get_type_connection_info(aas_model_type.__name__)
            for connection_info in connection_infos:
                connector = self.middleware.persistence_registry.get_connection(connection_info)
                retrieved_aas = await connector.provide()
                aas_list.append(retrieved_aas)
            return aas_list

        @router.post(f"/", response_model=Dict[str, str])
        async def post_item(item: aas_model_type) -> Dict[str, str]:
            try:
                await self.middleware.persist(data_model_name=self.data_model_name, model=item)
                return {
                    "message": f"Succesfully created aas {aas_model_type.__name__} with id {item.id}"
                }
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"AAS with id {item.id} already exists"
                )

        @router.get("/{item_id}", response_model=aas_model_type)
        async def get_item(item_id: str):
            try:
                connector = self.get_connector(item_id)
                provided_data = await connector.provide()
                # TODO: update that the correct type is immediately returned -> using model validate inside the connector
                provided_data_dict = provided_data.model_dump()
                return aas_model_type.model_validate(provided_data_dict)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"AAS with id {item_id} could not be retrieved. Error: {e}"
                )

        @router.put("/{item_id}")
        async def put_item(item_id: str, item: aas_model_type) -> Dict[str, str]:
            try:
                consumer = self.get_connector(item_id)
            except KeyError as e:
                raise HTTPException(
                    status_code=400, detail=f"AAS with id {item_id} could not be retrieved. Try posting it at first."
                )
        
            # TODO: add some exception handling below
            if item_id == item.id:
                await consumer.consume(item)
            else:
                await self.middleware.persist(data_model_name=self.data_model_name, model=item)     
                await delete_item(item_id)
                
            return {"message": f"Succesfully updated aas with id {item.id}"}

        @router.delete("/{item_id}")
        async def delete_item(item_id: str):
            await self.get_connector(item_id).consume(None)
            self.middleware.persistence_registry.remove_connection(ConnectionInfo(data_model_name=self.data_model_name, model_id=item_id))
            return {"message": f"Succesfully deleted aas with id {item_id}"}

        return router

    
    
    def generate_endpoints_from_model(self, pydantic_model: Type[BaseModel]) -> List[APIRouter]:
        """
        Generates CRUD endpoints for a pydantic model representing an aas and its submodels.

        Args:
            pydantic_model (Type[BaseModel]): Pydantic model representing an aas with submodels.

        Returns:
            List[APIRouter]: List of FastAPI routers with CRUD endpoints for the given pydantic model and its submodels that perform Middleware syxnchronization.
        """
        routers = []
        routers.append(self.generate_aas_endpoints_from_model(pydantic_model))
        attribute_infos = get_contained_models_attribute_info(pydantic_model)
        for attribute_name, contained_model in attribute_infos:
            routers.append(self.generate_endpoints_from_contained_model(pydantic_model, attribute_name, contained_model))
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