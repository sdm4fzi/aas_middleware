from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from pydantic.fields import ModelField

from typing import List, Type, Dict


# TODO: update imports
from aas2openapi.client.aas_client import (
    post_aas_to_server,
    put_aas_to_server,
    get_aas_from_server,
    delete_aas_from_server,
    get_all_aas_from_server,
)
from aas2openapi.client.submodel_client import (
    post_submodel_to_server,
    put_submodel_to_server,
    get_submodel_from_aas_id_and_class_name,
    delete_submodel_from_server,
)
from aas2openapi.models import base
from aas2openapi.util.client_utils import check_aas_and_sm_server_online
from aas2openapi.util.convert_util import (
    get_all_submodels_from_model,
    convert_camel_case_to_underscrore_str,
)
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder


def is_optional_field(field: ModelField):
    return field.required is False


async def update_aas_on_server(
    aas_id: str,
    aas_model: Type[base.AAS],
    submodel_class_name: str,
    submodel_model: Type[base.Submodel] = None,
):
    data_retrieved = await get_aas_from_server(aas_id)
    model_instance_data = data_retrieved.dict()
    submodel_instance_name = convert_camel_case_to_underscrore_str(submodel_class_name)

    if submodel_model:
        model_instance_data[submodel_instance_name] = submodel_model
    elif submodel_instance_name in model_instance_data:
        del model_instance_data[submodel_instance_name]
    new_model_instance = aas_model(**model_instance_data)

    await put_aas_to_server(new_model_instance)


def check_if_submodel_is_optional_in_aas(
    aas: Type[base.AAS], submodel: Type[base.Submodel]
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
    for field_name, field in aas.__fields__.items():
        if field.type_.__name__ == submodel.__name__:
            if is_optional_field(field):
                return True
            else:
                return False
    raise ValueError(
        f"Submodel {submodel.__name__} is not a submodel of {aas.__name__}."
    )


def generate_submodel_endpoints_from_model(
    pydantic_model: Type[BaseModel], submodel: Type[base.Submodel]
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
        await check_aas_and_sm_server_online()
        try:
            return await get_submodel_from_aas_id_and_class_name(item_id, submodel_name)
        except:
            raise HTTPException(
                status_code=411,
                detail=f"Submodel {submodel_name} does not exist for aas with id {item_id}.",
            )

    if optional_submodel:

        @router.post("/")
        async def post_item(item_id: str, item: submodel) -> Dict[str, str]:
            await check_aas_and_sm_server_online()
            try:
                await get_submodel_from_aas_id_and_class_name(item_id, submodel_name)
                raise HTTPException(
                    status_code=413,
                    detail=f"Submodel already exists for aas with id {item_id}. Use PUT method to update the submodel.",
                )
            except HTTPException as e:
                if e.status_code == 411:
                    await post_submodel_to_server(item)
                    await update_aas_on_server(
                        item_id, pydantic_model, submodel_name, item
                    )
                    return {
                        "message": f"Succesfully created submodel {submodel_name} of aas with id {item_id}"
                    }
                else:
                    raise e

    @router.put("/")
    async def put_item(item_id: str, item: submodel) -> Dict[str, str]:
        await check_aas_and_sm_server_online()
        submodel = await get_submodel_from_aas_id_and_class_name(item_id, submodel_name)
        await put_submodel_to_server(item)
        await update_aas_on_server(item_id, pydantic_model, submodel_name, item)
        return {
            "message": f"Succesfully updated submodel {submodel_name} of aas with id {item_id}"
        }

    if optional_submodel:

        @router.delete("/")
        async def delete_item(item_id: str):
            await check_aas_and_sm_server_online()
            submodel = await get_submodel_from_aas_id_and_class_name(
                item_id, submodel_name
            )
            await update_aas_on_server(item_id, pydantic_model, submodel_name)
            await delete_submodel_from_server(submodel.id)
            return {
                "message": f"Succesfully deleted submodel {submodel_name} of aas with id {item_id}"
            }

    return router


def generate_aas_endpoints_from_model(pydantic_model: Type[BaseModel]) -> APIRouter:
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
        await check_aas_and_sm_server_online()
        data_retrieved = await get_all_aas_from_server(pydantic_model)
        return data_retrieved

    @router.post(f"/")
    async def post_item(item: pydantic_model) -> Dict[str, str]:
        await check_aas_and_sm_server_online()
        await post_aas_to_server(item)
        return {"message": f"Created aas with id {item.id}"}

    @router.get("/{item_id}", response_model=pydantic_model)
    async def get_item(item_id: str):
        await check_aas_and_sm_server_online()
        data_retrieved = await get_aas_from_server(item_id)
        return data_retrieved

    @router.put("/{item_id}")
    async def put_item(item_id: str, item: pydantic_model) -> Dict[str, str]:
        await check_aas_and_sm_server_online()
        await put_aas_to_server(item)
        return {"message": f"Succesfully updated aas with id {item.id}"}

    @router.delete("/{item_id}")
    async def delete_item(item_id: str):
        await check_aas_and_sm_server_online()
        await delete_aas_from_server(item_id)
        return {"message": f"Succesfully deleted aas with id {item_id}"}

    return router


def generate_endpoints_from_model(pydantic_model: Type[BaseModel]) -> List[APIRouter]:
    """
    Generates CRUD endpoints for a pydantic model representing an aas and its submodels.

    Args:
        pydantic_model (Type[BaseModel]): Pydantic model representing an aas with submodels.

    Returns:
        List[APIRouter]: List of FastAPI routers with CRUD endpoints for the given pydantic model and its submodels that perform Middleware syxnchronization.
    """
    routers = []
    routers.append(generate_aas_endpoints_from_model(pydantic_model))
    submodels = get_all_submodels_from_model(pydantic_model)
    for submodel in submodels:
        routers.append(generate_submodel_endpoints_from_model(pydantic_model, submodel))

    return routers

def generate_endpoints_from_data_model(data_model: DataModel) -> List[APIRouter]:
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
        routers += generate_endpoints_from_model(top_level_model_type)

    return routers
