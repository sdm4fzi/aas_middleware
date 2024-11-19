from types import NoneType
import typing
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.formatting.aas.aas_model import Blob, File, Submodel
from aas_middleware.model.schema_util import get_attribute_dict_of_schema


def get_path_to_top_level_model_instance(item_id: str, data_model: DataModel) -> list[str]:
    model = data_model.get_model(item_id)
    if not model:
        return []
    path = [item_id]
    for referencing_info in data_model.get_referencing_info(model):
        path.extend(
            get_path_to_top_level_model_instance(referencing_info.identifiable_id, data_model)
        )
    return path


def get_instance_paths_to_item_type(
    item_type: type, data_model: DataModel
) -> dict[str, list[str]]:
    """
    Returns the dict with item_id paths from the top level models to all instances of the item type.

    Args:
        item_type (type): The type of the items.
        data_model (DataModel): The data model.

    Returns:
        dict[str, list[str]]: The dict with item_id paths.
    """
    if not item_type in data_model._models_key_type:
        return {}
    paths = {}
    for item_id in data_model._models_key_type[item_type]:
        path = get_path_to_top_level_model_instance(item_id, data_model)
        if path:
            paths[item_id] = path
    return paths


def get_paths_to_type(type: type, data_model: DataModel) -> list[list[str]]:
    """
    Returns the list of type paths to the type.

    Args:
        type (type): The type to find paths to.
        data_model (DataModel): The data model.

    Returns:
        list[list[str]]: A list of paths from top level type to the specified type.
    """
    if not type.__name__ in data_model._schemas:
        return []
    pointer_paths = []
    for referencing_info in data_model.get_schema_referencing_info(type):
        referncing_schema = data_model._schemas[referencing_info.identifiable_id]
        referencing_schema_pointer_paths = get_paths_to_type(
            referncing_schema, data_model
        )
        for path in referencing_schema_pointer_paths:
            pointer_paths.append(path + [type.__name__])
    if not pointer_paths:
        pointer_paths.append([type.__name__])
    return pointer_paths


def get_paths_to_contained_type(
    type: type,
    contained_type: type,
) -> list[list[str]]:
    data_model = DataModel.from_model_types(type)
    return get_paths_to_type(contained_type, data_model)


def get_attribute_paths_to_type(type: type, data_model: DataModel) -> list[list[str]]:
    """
    Returns the list of attribute paths to the type.

    Args:
        type (type): The type to find paths to.
        data_model (DataModel): The data model.

    Returns:
        list[list[str]]: A list of paths from top level type to the specified type.
    """
    if not type.__name__ in data_model._schemas:
        return []
    pointer_paths = []
    for referencing_info in data_model.get_schema_referencing_info(type):
        referncing_schema = data_model._schemas[referencing_info.identifiable_id]
        for attribute_name, attribute in get_attribute_dict_of_schema(
            referncing_schema
        ).items():
            if typing.get_origin(attribute) == typing.Union and NoneType in typing.get_args(
                attribute
            ):
                attribute_types = typing.get_args(attribute)
                if not type in attribute_types:
                    continue
                attribute = type
            if not attribute == type:
                continue
            attribute_pointer_path = get_attribute_paths_to_type(
                referncing_schema, data_model
            )
            for pointer_path in attribute_pointer_path:
                pointer_paths.append(pointer_path + [attribute_name])

    if not pointer_paths:
        pointer_paths.append([type.__name__])

    return pointer_paths


def get_attribute_paths_to_contained_type(
    type: type,
    contained_type: type,
) -> list[list[str]]:
    if typing.get_origin(type) == typing.Union and NoneType in typing.get_args(type):
        type = typing.get_args(type)[0]
    data_model = DataModel.from_model_types(type)
    attribute_paths = get_attribute_paths_to_type(contained_type, data_model)
    new_attribute_paths = []
    for attribute_path in attribute_paths:
        assert attribute_path[0] == type.__name__, f"Expected {type.__name__}, got {attribute_path[0]}"
        new_attribute_paths.append(attribute_path[1:])
    return new_attribute_paths
