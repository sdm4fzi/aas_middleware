from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from aas_middleware.connect.connectors.aas_client_connector import client_utils
from aas_middleware.model.data_model import DataModel
from aas_pydantic import aas_model

from ba_syx_aas_environment_component_client import Client as SubmodelClient
from ba_syx_aas_environment_component_client.api.submodel_repository_api import (
    delete_submodel_by_id,
    get_all_submodels,
    get_submodel_by_id,
    post_submodel,
    put_submodel_by_id,
)
from ba_syx_aas_environment_component_client.models.submodel import (
    Submodel as ClientSubmodel,
)
from basyx.aas import model as basyx_model

# from aas_middleware.model.formatting.aas.convert_aas import convert_submodel_to_model
# from aas_middleware.model.formatting.aas.convert_pydantic import convert_model_to_submodel
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxFormatter
from aas_pydantic.convert_aas_instance import (
    convert_submodel_to_model_instance,
)
from aas_pydantic.convert_pydantic_model import (
    convert_model_to_submodel,
)


async def get_basyx_submodel_from_server(
    submodel_id: str, submodel_client: SubmodelClient
) -> basyx_model.Submodel:
    """
    Function to get a submodel from the server
    Args:
        submodel_id (str): id of the submodel
        submodel_client (SubmodelClient): client to connect to the server

    Returns:
        model.Submodel: submodel retrieved from the server

    Raises:
        HTTPException: If submodel with the given id does not exist
    """
    base_64_id = client_utils.get_base64_from_string(submodel_id)
    try:
        submodel_data = await get_submodel_by_id.asyncio(
            client=submodel_client, submodel_identifier=base_64_id
        )
        return client_utils.transform_client_to_basyx_model(submodel_data.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Submodel with id {submodel_id} could not be retrieved. Error: {e}",
        )


async def get_all_basyx_submodels_from_server(
    aas: basyx_model.AssetAdministrationShell, submodel_client: SubmodelClient
) -> List[ClientSubmodel]:
    """
    Function to get all submodels from an AAS in basyx format
    Args:
        aas (model.AssetAdministrationShell): AAS to get submodels from
        submodel_client (SubmodelClient): client to connect to the server

    Returns:
        List[model.Submodel]: List of basyx submodels retrieved from the server
    """
    submodels = []
    for submodel_reference in aas.submodel:
        basyx_submodel = await get_basyx_submodel_from_server(
            submodel_reference.key[0].value, submodel_client
        )
        submodels.append(basyx_submodel)
    return submodels


async def submodel_is_on_server(
    submodel_id: str, submodel_client: SubmodelClient
) -> bool:
    """
    Function to check if a submodel with the given id is on the server
    Args:
        submodel_id (str): id of the submodel
        submodel_client (SubmodelClient): client to connect to the server

    Returns:
        bool: True if submodel is on server, False if not
    """
    try:
        await get_submodel_from_server(submodel_id, submodel_client)
        return True
    except HTTPException as e:
        return False


async def post_submodel_to_server(
    pydantic_submodel: aas_model.Submodel, submodel_client: SubmodelClient
):
    """
    Function to post a submodel to the server
    Args:
        pydantic_submodel (aas_model.Submodel): submodel to post
        submodel_client (SubmodelClient): client to connect to the server

    Raises:
        HTTPException: If submodel with the given id already exists
    """
    if await submodel_is_on_server(pydantic_submodel.id, submodel_client):
        raise HTTPException(
            status_code=400,
            detail=f"Submodel with id {pydantic_submodel.id} already exists. Try putting it instead.",
        )
    basyx_submodel = convert_model_to_submodel(pydantic_submodel)
    submodel_for_client = client_utils.ClientModel(basyx_object=basyx_submodel)
    # TODO: make a try except with json.decoder.JSONDecodeError to avoid error when posting a submodel that already exists, same goes for aas
    response = await post_submodel.asyncio(
        client=submodel_client, body=submodel_for_client
    )


async def put_submodel_to_server(
    submodel: aas_model.Submodel, submodel_client: SubmodelClient
):
    """
    Function to put a submodel to the server
    Args:
        submodel (aas_model.Submodel): submodel to put
        submodel_client (SubmodelClient): client to connect to the server

    Raises:
        HTTPException: If submodel with the given id does not exist
    """
    if not await submodel_is_on_server(submodel.id, submodel_client):
        raise HTTPException(
            status_code=400,
            detail=f"Submodel with id {submodel.id} does not exist. Try posting it first.",
        )
    basyx_submodel = convert_model_to_submodel(submodel)
    submodel_for_client = client_utils.ClientModel(basyx_object=basyx_submodel)
    base_64_id = client_utils.get_base64_from_string(submodel.id)
    response = await put_submodel_by_id.asyncio(
        submodel_identifier=base_64_id, client=submodel_client, body=submodel_for_client
    )


async def get_submodel_from_server(
    submodel_id: str,
    submodel_client: SubmodelClient,
    submodel_type: Optional[aas_model.Submodel] = None,
) -> aas_model.Submodel:
    """
    Function to get a submodel from the server
    Args:
        submodel_id (str): id of the submodel
        submodel_client (SubmodelClient): client to connect to the server
        submodel_type (aas_model.Submodel): Pydantic model of the submodel
    Returns:
        aas_model.Submodel: submodel retrieved from the server

    Raises:
        HTTPException: If submodel with the given id does not exist
    """
    try:
        basyx_submodel = await get_basyx_submodel_from_server(
            submodel_id, submodel_client
        )
        return convert_submodel_to_model_instance(basyx_submodel, submodel_type)
    except HTTPException as e:
        raise HTTPException(
            status_code=400,
            detail=f"Submodel with id {submodel_id} could not be retrieved. Error: {e}",
        )


async def get_all_submodel_data_from_server(
    submodel_client: SubmodelClient,
) -> List[ClientSubmodel]:
    """
    Function to get all submodels from the server
    Returns:
        List[aas_model.Submodel]: List of submodels retrieved from the server
    """
    submodel_data = await get_all_submodels.asyncio(client=submodel_client)
    submodel_data = submodel_data.result
    return submodel_data


async def get_all_submodels_of_type(
    model: BaseModel,
    submodel_client: SubmodelClient,
    submodel_types: Optional[list[aas_model.Submodel]] = None,
) -> DataModel:
    """
    Function to get all submodels of a certain type from the server
    Args:
        model (BaseModel): Pydantic model of the submodel
        submodel_client (SubmodelClient): client to connect to the server
        submodel_type (aas_model.Submodel): Pydantic model of the submodel

    Returns:
        List[aas_model.Submodel]: List of submodels retrieved from the server
    """
    submodels_data = await get_all_submodel_data_from_server(submodel_client)
    submodels_list = [
        client_utils.transform_client_to_basyx_model(submodel_data)
        for submodel_data in submodels_data
    ]
    obj_store = basyx_model.DictObjectStore()
    [obj_store.add(submodel) for submodel in submodels_list]

    data_model = BasyxFormatter().deserialize(obj_store, submodel_types)
    return data_model


async def delete_submodel_from_server(
    submodel_id: str, submodel_client: SubmodelClient
):
    """
    Function to delete a submodel from the server
    Args:
        submodel_id (str): id of the submodel
        submodel_client (SubmodelClient): client to connect to the server

    Raises:
        HTTPException: If submodel with the given id does not exist
    """
    if not await submodel_is_on_server(submodel_id, submodel_client):
        raise HTTPException(
            status_code=400,
            detail=f"Submodel with id {submodel_id} does not exist. Cannot delete it.",
        )
    base_64_id = client_utils.get_base64_from_string(submodel_id)
    await delete_submodel_by_id.asyncio(
        client=submodel_client, submodel_identifier=base_64_id
    )
