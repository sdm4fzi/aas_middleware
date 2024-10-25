from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder
from aas_middleware.model.formatting.aas import aas_model
from aas_middleware.model.formatting.aas.convert_pydantic_type import logger


from typing import List, Tuple


def infere_aas_structure(
    data: DataModel,
) -> Tuple[List[aas_model.AAS], List[aas_model.Submodel]]:
    """
    The function assert that the data contained in the data model fulfills the aas meta model structure.

    Args:
        data (DataModel): The Data Model containing the objects that should be transformed to AAS models

    Returns:
        Tuple[List[aas_model.AAS], List[aas_model.Submodel]]: Tuple with AAS models and Submodel models
    """
    if all(all(isinstance(model, aas_model.AAS) for model in model_items) for model_items in data.get_top_level_models().values()):
        top_level_models_list = []
        for models in data.get_top_level_models().values():
            top_level_models_list += models
        return top_level_models_list, []
    logger.warning(
        "The data model does not contain only AAS models. Trying to infer the AAS structure by rebuilding the data model."
    )
    new_data_model = DataModelRebuilder(data).rebuild_data_model_for_AAS_structure()
    top_level_models_list = []
    for models in new_data_model.get_top_level_models().values():
        top_level_models_list += models
    aas_models = [
        model for model in top_level_models_list if isinstance(model, aas_model.AAS)
    ]
    submodel_models = [
        model
        for model in top_level_models_list
        if isinstance(model, aas_model.Submodel)
    ]
    return aas_models, submodel_models