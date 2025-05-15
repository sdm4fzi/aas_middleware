import typing
import aiohttp
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from pydantic import BaseModel

from typing import TYPE_CHECKING, List, Type, Dict, Union
from aas_middleware.connect.connectors.connector import Connector
from aas_middleware.middleware import middleware
from aas_middleware.middleware.registries import ConnectionInfo
from aas_middleware.model import data_model
from aas_middleware.model.core import Identifiable
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.formatting.aas.aas_middleware_util import (
    get_contained_models_attribute_info,
)
from aas_pydantic.aas_model import Blob, File
from aas_middleware.model.reference_util import (
    get_attribute_paths_to_contained_type,
)
from aas_middleware.model.util import is_identifiable_type

if TYPE_CHECKING:
    from aas_middleware.middleware.middleware import Middleware


def check_if_attribute_is_optional(model: Type[Identifiable], attribute_name: str) -> bool:
    """
    Checks if the attribute of a model is optional.

    Args:
        model (Type[Identifiable]): Pydantic model.
        attribute_name (str): Name of the attribute.

    Returns:
        bool: True if the attribute is optional, False otherwise.

    Raises:
        ValueError: If the attribute is not present in the model.
    """
    if attribute_name not in model.model_fields:
        raise ValueError(
            f"{attribute_name} is not an attribute of {model.__name__}."
        )
    field_info = model.model_fields[attribute_name]
    if not field_info.is_required():
        return True
    elif typing.get_origin(field_info.annotation) == Union and type(
        None
    ) in typing.get_args(field_info.annotation):
        return True
    else:
        return False


def check_if_attribute_is_iterable(model: Type[Identifiable], attribute_name: str) -> bool:
    """
    Checks if an an attribute is iterable. Sets are not considered iterable, since they do not allow indexing.
    This is important for the CRUD endpoints, since they are generated for lists and tuples.
    Args:
        model (Type[Identifiable]): the model to check.
        attribute_name (str): the name of the attribute to check.

    Returns:
        bool: True if the attribute is iterable, False otherwise.

    Raises:
        ValueError: If the attribute is not in the model.
    """
    if attribute_name not in model.model_fields:
        raise ValueError(
            f"{attribute_name} is not an attribute of {model.__name__}."
        )
    field_info = model.model_fields[attribute_name]
    if typing.get_origin(field_info.annotation) == Union:
        all_args_are_iterable = False
        for arg in typing.get_args(field_info.annotation):
            if arg is type(None):
                continue
            elif typing.get_origin(arg) in (list, tuple):
                all_args_are_iterable = True
            else:
                all_args_are_iterable = False
        return all_args_are_iterable
    elif typing.get_origin(field_info.annotation) in (list, tuple):
        return True
    else:
        return False


def remove_blob_contents(model: BaseModel, blob_paths: list[list[str]]) -> BaseModel:
    """
    Removes the content of all blob attributes of a model and returns a copy of it.

    Args:
        model (BaseModel): Model with blob attributes.
        blob_paths (list[list[str]]): List of paths to the blob attributes.

    Returns:
        BaseModel: Copy of the model with the content of all blob attributes removed.
    """
    model = model.model_copy(deep=True)
    for blob_path in blob_paths:
        contained_model = model
        for path_element in blob_path:
            contained_model = getattr(contained_model, path_element)
        if isinstance(contained_model, Blob):
            contained_model.content = None
    return model


class RestRouter:
    def __init__(
        self, data_model: DataModel, data_model_name: str, middleware: "Middleware"
    ):
        self.data_model = data_model
        self.data_model_name = data_model_name
        self.aas_data_model = data_model

        self.middleware = middleware

    def get_connector(self, item_id: str) -> Connector:
        return self.middleware.persistence_registry.get_connection(
            ConnectionInfo(data_model_name=self.data_model_name, model_id=item_id)
        )

    def generate_endpoints_from_contained_model(
        self,
        top_level_model: Type[Identifiable],
        attribute_name: str,
        contained_model: Type[Identifiable],
    ) -> APIRouter:
        """
        Generates CRUD endpoints for a contained model of an Identifiable model.

        Args:
            aas_model_type (Type[Identifiable]): Pydantic model representing the top level model.
            contained_model (Type[Identifiable]): Pydantic model representing the contained model.

        Returns:
            APIRouter: FastAPI router with CRUD endpoints for the given contained model that performs Middleware synchronization.
        """
        model_name = top_level_model.__name__
        is_optional_contained_model = check_if_attribute_is_optional(
            top_level_model, attribute_name
        )
        is_iterable_contained_model = check_if_attribute_is_iterable(
            top_level_model, attribute_name
        )

        # TODO: consider data model name in url of the model endpoints
        router = APIRouter(
            prefix=f"/{model_name}/{{item_id}}/{attribute_name}",
            tags=[model_name],
            responses={404: {"description": "Not found"}},
        )

        file_paths = get_attribute_paths_to_contained_type(contained_model, File)
        blob_paths = get_attribute_paths_to_contained_type(contained_model, Blob)

        @router.get(
            "/",
            response_model=contained_model,
        )
        async def get_item(item_id: str):
            try:
                top_level_model = await self.get_connector(item_id).provide()
                contained_model = getattr(top_level_model, attribute_name)
                if is_identifiable_type(contained_model):
                    contained_model = remove_blob_contents(contained_model, blob_paths)
                return contained_model
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Submodel with id {item_id} could not be retrieved. Error: {e}",
                )

        if is_optional_contained_model:
            @router.post("/")
            async def post_item(
                item_id: str, item: contained_model # type: ignore
            ) -> Dict[str, str]:
                connector = self.get_connector(item_id)
                try:
                    provided_data: Identifiable = await connector.provide()
                    provided_data_dict = provided_data.model_dump()
                    top_level_model_instance = top_level_model.model_validate(provided_data_dict)
                    setattr(top_level_model_instance, attribute_name, item)
                    await connector.consume(top_level_model_instance)
                    return {
                        "message": f"Succesfully created attribute {attribute_name} of aas with id {item_id}"
                    }
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Attribute {attribute_name} for model with id {item_id} could not be set. Error: {e}",
                    )

        @router.put("/")
        async def put_item(item_id: str, item: contained_model) -> Dict[str, str]: # type: ignore
            connector = self.get_connector(item_id)
            try:
                top_level_model_instance: Identifiable = await connector.provide()
                if getattr(top_level_model_instance, attribute_name) == item:
                    return {
                        "message": f"Attribute {attribute_name} of model with id {item_id} is already up to date"
                    }
                setattr(top_level_model_instance, attribute_name, item)
                await connector.consume(top_level_model_instance)
                return {
                    "message": f"Succesfully updated attribute {attribute_name} of model with id {item_id}"
                }
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Attribute {attribute_name} of model with id {item_id} could not be updated. Error: {e}",
                )

        if is_optional_contained_model:

            @router.delete("/")
            async def delete_item(item_id: str):
                connector = self.get_connector(item_id)
                try:
                    top_level_model_instance: Identifiable = await connector.provide()
                    setattr(top_level_model_instance, attribute_name, None)
                    await connector.consume(top_level_model_instance)
                    return {
                        "message": f"Succesfully deleted attribute {attribute_name} of model with id {item_id}"
                    }
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"attribute {attribute_name} of model with id {item_id} could not be deleted. Error: {e}",
                    )

        if file_paths:
            for file_path in file_paths:
                self.generate_endpoints_for_file_path(
                    router, attribute_name, contained_model, file_path
                )

        if blob_paths:
            for blob_path in blob_paths:
                self.generate_endpoints_for_blob_path(
                    router, attribute_name, contained_model, blob_path
                )

        return router

    def generate_endpoints_for_file_path(
        self,
        router: APIRouter,
        attribute_name: str,
        contained_model_type: Type[Identifiable],
        file_path: list[str],
    ):
        """
        Generates CRUD endpoints for a file path of a File of an Identifiable model.

        Args:
            router (APIRouter): FastAPI router with CRUD endpoints for the given contained model that performs Middleware synchronization.
            attribute_name (str): The name of the attribute with the contained model.
            contained_model_type (Type[Identifiable]): Pydantic model representing the contained model.
            file_path (list[str]): The path to the file attribute of the contained model.

        Returns:    
            APIRouter: FastAPI router with CRUD endpoints for the given file path that performs Middleware synchronization.
        """
        url_file_path = "/".join(file_path)
        file_path.insert(0, attribute_name)

        @router.get(
            f"/{url_file_path}",
            # response_class=RedirectResponse
        )
        async def get_item(item_id: str):
            try:
                model = await self.get_connector(item_id).provide()
                contained_model = model
                for path_element in file_path:
                    contained_model = getattr(contained_model, path_element)
                assert isinstance(contained_model, File)
                async with aiohttp.ClientSession() as session:
                    async with session.get(contained_model.path) as response:
                        content = await response.read()
                return Response(content=content, media_type=contained_model.media_type)

            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model with id {item_id} could not be retrieved. Error: {e}",
                )

    def generate_endpoints_for_blob_path(
        self,
        router: APIRouter,
        attribute_name: str,
        contained_model_type: Type[Identifiable],
        blob_path: list[str],
    ):
        """
        Generates CRUD endpoints for a file path of a Blob of an Identifiable model.

        Args:
            router (APIRouter): FastAPI router with CRUD endpoints for the given contained model that performs Middleware synchronization.
            attribute_name (str): The name of the attribute with the contained model.
            contained_model_type (Type[Identifiable]): Pydantic model representing the contained model.
            blob_path (list[str]): The path to the blob attribute of the contained model.

        Returns:
            APIRouter: FastAPI router with CRUD endpoints for the given blob path that performs Middleware synchronization.
        """
        url_blob_path = "/".join(blob_path)
        blob_path.insert(0, attribute_name)

        @router.get(f"/{url_blob_path}")
        async def get_item(item_id: str):
            try:
                model = await self.get_connector(item_id).provide()
                contained_model = model
                for path_element in blob_path:
                    contained_model = getattr(contained_model, path_element)
                assert isinstance(contained_model, Blob)
                return Response(
                    content=contained_model.content,
                    media_type=contained_model.media_type,
                )

            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model with id {item_id} could not be retrieved. Error: {e}",
                )

    def generate_aas_endpoints_from_model(self, model_type: Type[Identifiable]) -> APIRouter:
        """
        Generates CRUD endpoints for a pydantic model representing an Identifiable model.

        Args:
            model_type (Type[Identifiable]): Identifiable model.

        Returns:
            APIRouter: FastAPI router with CRUD endpoints for the given pydantic model that performs Middleware synchronization.
        """
        router = APIRouter(
            prefix=f"/{model_type.__name__}",
            tags=[model_type.__name__],
            responses={404: {"description": "Not found"}},
        )

        blob_paths = get_attribute_paths_to_contained_type(model_type, Blob)

        @router.get("/", response_model=List[model_type])
        async def get_items():
            model_instance_list = []
            connection_infos = (
                self.middleware.persistence_registry.get_type_connection_info(
                    model_type.__name__
                )
            )
            for connection_info in connection_infos:
                connector = self.middleware.persistence_registry.get_connection(
                    connection_info
                )
                retrieved_model_instance = await connector.provide()
                retrieved_model_instance = remove_blob_contents(retrieved_model_instance, blob_paths)
                model_instance_list.append(retrieved_model_instance)
            return model_instance_list

        @router.post(f"/", response_model=Dict[str, str])
        async def post_item(item: model_type) -> Dict[str, str]: # type: ignore
            try:
                await self.middleware.persist(
                    data_model_name=self.data_model_name, model=item
                )
                return {
                    "message": f"Succesfully created Model {model_type.__name__} with id {item.id}"
                }
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Model with id {item.id} already exists. Try updating it instead."
                )

        @router.get("/{item_id}", response_model=model_type)
        async def get_item(item_id: str):
            try:
                connector = self.get_connector(item_id)
                provided_data: Identifiable = await connector.provide()
                provided_data_dict = provided_data.model_dump()
                model_instance = model_type.model_validate(provided_data_dict)
                model_instance = remove_blob_contents(model_instance, blob_paths)
                return model_instance
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model with id {item_id} could not be retrieved. Error: {e}",
                )

        @router.put("/{item_id}")
        async def put_item(item_id: str, item: model_type) -> Dict[str, str]: # type: ignore
            try:
                consumer = self.get_connector(item_id)
            except KeyError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model with id {item_id} could not be retrieved. Try posting it at first.",
                )
            try:
                if item_id == item.id:
                    await consumer.consume(item)
                else:
                    await self.middleware.persist(
                        data_model_name=self.data_model_name, model=item
                    )
                    await delete_item(item_id)

                return {"message": f"Succesfully updated Model with id {item.id}"}
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model with id {item_id} could not be updated. Error: {e}",
                )

        @router.delete("/{item_id}")
        async def delete_item(item_id: str):
            await self.get_connector(item_id).consume(None)
            self.middleware.persistence_registry.remove_connection(
                ConnectionInfo(data_model_name=self.data_model_name, model_id=item_id)
            )
            return {"message": f"Succesfully deleted Model with id {item_id}"}

        return router

    def generate_endpoints_from_model(
        self, identifiable: Type[Identifiable]
    ) -> List[APIRouter]:
        """
        Generates CRUD endpoints for a pydantic model representing an aas and its submodels.

        Args:
            pydantic_model (Type[BaseModel]): Pydantic model representing an aas with submodels.

        Returns:
            List[APIRouter]: List of FastAPI routers with CRUD endpoints for the given pydantic model and its submodels that perform Middleware syxnchronization.
        """
        routers = []
        routers.append(self.generate_aas_endpoints_from_model(identifiable))
        attribute_infos = get_contained_models_attribute_info(identifiable)
        for attribute_name, contained_model in attribute_infos:
            routers.append(
                self.generate_endpoints_from_contained_model(
                    identifiable, attribute_name, contained_model
                )
            )
        return routers

    def generate_endpoints(self):
        """
        Generates CRUD endpoints for a pydantic model representing an aas and its submodels and adds them to the middleware app.
        """
        routers = []

        for top_level_model_type in self.aas_data_model.get_top_level_types():
            routers += self.generate_endpoints_from_model(top_level_model_type)
        for router in routers:
            self.middleware.app.include_router(router)
