from __future__ import annotations

import os
from typing import List, Optional
from basyx.aas import model

from pydantic import BaseModel

from aas_middleware.connect.connectors.aas_client_connector import client_utils
from aas_middleware.connect.connectors.aas_client_connector.submodel_client import (
    get_all_basyx_submodels_from_server,
    get_submodel_from_server,
    post_submodel_to_server,
    put_submodel_to_server,
    submodel_is_on_server,
)
from aas_middleware.model.data_model import DataModel
from aas_pydantic import aas_model

from ba_syx_aas_environment_component_client import Client as AASClient
from ba_syx_aas_environment_component_client import Client as SubmodelClient
from ba_syx_aas_environment_component_client.api.asset_administration_shell_repository_api import (
    delete_asset_administration_shell_by_id,
    get_all_asset_administration_shells,
    get_asset_administration_shell_by_id,
    post_asset_administration_shell,
    put_asset_administration_shell_by_id,
)
from fastapi import HTTPException

from aas_middleware.connect.connectors.aas_client_connector.aas_client_model import (
    ClientModel,
)
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxFormatter
from aas_pydantic.convert_pydantic_model import (
    convert_model_to_aas,
)
from aas_middleware.model.util import get_value_attributes

import logging

logger = logging.getLogger(__name__)


async def aas_is_on_server(aas_id: str, aas_client: AASClient) -> bool:
    """
    Function to check if an AAS with the given id is on the server
    Args:
        aas_id (str): id of the AAS
    Returns:
        bool: True if AAS is on server, False if not
    """
    try:
        await get_basyx_aas_from_server(aas_id, aas_client)
        return True
    except Exception as e:
        return False


def check_aas_for_duplicate_ids(aas: aas_model.AAS):
    ids = {aas.id}
    for attribute_name, attribute_value in get_value_attributes(aas).items():
        if not hasattr(attribute_value, "id"):
            continue
        if attribute_value.id in ids:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate id <{attribute_value.id}> in AAS <{aas.id}> of type <{aas.__class__.__name__}> for attribute <{attribute_name}>.",
            )
        ids.add(attribute_value.id)


async def post_aas_to_server(
    aas: aas_model.AAS, aas_client: AASClient, submodel_client: SubmodelClient
):
    """
    Function to post an AAS to the server. Also posts all submodels of the AAS to the server, if they do not exist yet.
    Args:
        aas (aas_model.AAS): AAS to post
    Raises:
        HTTPException: If AAS with the given id already exists
    """
    if await aas_is_on_server(aas.id, aas_client):
        raise HTTPException(
            status_code=400, detail=f"AAS with id {aas.id} already exists"
        )
    check_aas_for_duplicate_ids(aas)
    obj_store = convert_model_to_aas(aas)
    basyx_aas = obj_store.get(aas.id)
    aas_for_client = ClientModel(basyx_object=basyx_aas)
    response = await post_asset_administration_shell.asyncio(
        client=aas_client, body=aas_for_client
    )

    aas_attributes = get_value_attributes(aas)
    for submodel in aas_attributes.values():
        if not await submodel_is_on_server(submodel.id, submodel_client):
            await post_submodel_to_server(submodel, submodel_client)
        else:
            logger.info(
                f"Submodel with id {submodel.id} already exists on the server. Updating the value."
            )
            await put_submodel_to_server(submodel, submodel_client)


async def put_aas_to_server(
    aas: aas_model.AAS, aas_client: AASClient, submodel_client: SubmodelClient
):
    """
    Function to put an AAS to the server
    Args:
        aas (aas_model.AAS): AAS to put
    Raises:
        HTTPException: If AAS with the given id does not exist
    """
    if not await aas_is_on_server(aas.id, aas_client):
        raise HTTPException(
            status_code=400, detail=f"AAS with id {aas.id} does not exist"
        )
    obj_store = convert_model_to_aas(aas)
    basyx_aas = obj_store.get(aas.id)
    aas_for_client = ClientModel(basyx_object=basyx_aas)
    base_64_id = client_utils.get_base64_from_string(aas.id)
    await put_asset_administration_shell_by_id.asyncio(
        aas_identifier=base_64_id, client=aas_client, body=aas_for_client
    )

    for submodel in get_value_attributes(aas).values():
        if await submodel_is_on_server(submodel.id, submodel_client):
            await put_submodel_to_server(submodel, submodel_client)
        else:
            await post_submodel_to_server(submodel, submodel_client)


async def get_basyx_aas_from_server(
    aas_id: str, aas_client: AASClient
) -> model.AssetAdministrationShell:
    """
    Function to get an AAS from the server
    Args:
        aas_id (str): id of the AAS
    Raises:
        HTTPException: If AAS with the given id does not exist
    Returns:
        model.AssetAdministrationShell: AAS retrieved from the server
    """
    base_64_id = client_utils.get_base64_from_string(aas_id)
    try:
        aas_data = await get_asset_administration_shell_by_id.asyncio(
            client=aas_client, aas_identifier=base_64_id
        )
        return client_utils.transform_client_to_basyx_model(aas_data.to_dict())
    except Exception as e:
        raise ConnectionError(e)


async def get_aas_from_server(
    aas_id: str,
    aas_client: AASClient,
    submodel_client: SubmodelClient,
    aas_type: Optional[aas_model.AAS] = None,
) -> aas_model.AAS:
    """
    Function to get an AAS from the server
    Args:
        aas_id (str): id of the AAS
    Returns:
        aas_model.AAS: AAS retrieved from the server

    Raises:
        HTTPException: If AAS with the given id does not exist
    """
    try:
        aas = await get_basyx_aas_from_server(aas_id, aas_client)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"AAS with id {aas_id} could not be retrieved. Error: {e}",
        )
    try:
        aas_submodels = await get_all_basyx_submodels_from_server(aas, submodel_client)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Submodels of AAS with id {aas_id} could not be retrieved. Error: {e}",
        )

    obj_store = model.DictObjectStore()
    obj_store.add(aas)
    [obj_store.add(submodel) for submodel in aas_submodels]

    data_model = BasyxFormatter().deserialize(obj_store, [aas_type])
    model_data = data_model.get_model(aas_id)

    return model_data


async def get_all_aas_from_server(
    aas_client: AASClient,
    submodel_client: SubmodelClient,
    types: Optional[list[type[aas_model.Submodel]]] = None,
) -> DataModel:
    """
    Function to get all AAS from the server
    Returns:
        List[aas_model.AAS]: List of AAS retrieved from the server
    """
    result_string = await get_all_asset_administration_shells.asyncio(client=aas_client)
    aas_data = result_string["result"]
    aas_list = [client_utils.transform_client_to_basyx_model(aas) for aas in aas_data]

    submodels = []
    for aas in aas_list:
        aas_submodels = await get_all_basyx_submodels_from_server(aas, submodel_client)
        submodels.extend(aas_submodels)
    obj_store = model.DictObjectStore()
    [obj_store.add(aas) for aas in aas_list]
    [
        obj_store.add(submodel)
        for submodel in submodels
        if not any(submodel.id == other_sm.id for other_sm in obj_store)
    ]

    data_model = BasyxFormatter().deserialize(obj_store, types)
    return data_model


async def delete_aas_from_server(aas_id: str, aas_client: AASClient):
    """
    Function to delete an AAS from the server
    Args:
        aas_id (str): id of the AAS

    Raises:
        HTTPException: If AAS with the given id does not exist
    """
    if not await aas_is_on_server(aas_id, aas_client):
        raise HTTPException(
            status_code=400,
            detail=f"AAS with id {aas_id} does not exist. Cannot delete it.",
        )
    base_64_id = client_utils.get_base64_from_string(aas_id)
    response = await delete_asset_administration_shell_by_id.asyncio(
        client=aas_client, aas_identifier=base_64_id
    )


async def get_submodel_from_aas_id_and_class_name(
    aas_id: str, class_name: str, aas_client: AASClient, submodel_client: SubmodelClient
) -> aas_model.Submodel:
    """
    Function to get a submodel from the server based on the AAS id and the class name of the submodel
    Args:
        aas_id (str): id of the AAS
        class_name (str): class name of the submodel
    Raises:
        HTTPException: If submodel with the given class name does not exist for the given AAS
    Returns:
        aas_model.Submodel: submodel retrieved from the server
    """
    basyx_aas = await get_basyx_aas_from_server(aas_id, aas_client)
    for basyx_submodel in basyx_aas.submodel:
        submodel_id = basyx_submodel.key[0].value
        submodel = await get_submodel_from_server(submodel_id, submodel_client)
        if submodel.__class__.__name__ == class_name:
            return submodel
    raise HTTPException(
        status_code=411,
        detail=f"Submodel with name {class_name} does not exist for AAS with id {aas_id}",
    )
