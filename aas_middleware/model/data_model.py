from __future__ import annotations

import json
from typing import Dict, List, Set, TypeVar, Union, Any, Type
from datetime import datetime

from aas_middleware.model.core import Referable

from aas_middleware.model.util import (
    convert_under_score_to_camel_case_str,
    convert_camel_case_to_underscrore_str,
)

from aas_middleware.model.util import (
    get_all_contained_referables,
    get_referable_attributes_of_model,
    assure_id_short_attribute,
    replace_attribute_with_model,
    get_referenced_ids_of_model,
)


NESTED_DICT = Dict[str, Union[Any, "NESTED_DICT"]]
T = TypeVar("T", bound=Referable)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


class DataModel:
    """
    The data model is a container that allows to store all models of a data model and provides methods to access them easily by their id or type.

    Args:
        *models (Union[List[Referable], Referable]): The models to load into the data model.
    """

    # TODO: change that models can also be objects, however, when inserting them, their are checked if they are identifiable
    # TODO: make Data model to be a BaseModel, to easily define other data models based on this by inheritance (similar to pydantic BaseModels)
    # TODO: if DataModels are passed to the data model init, their attributes are used.
    # TODO: build a graph with the models and their references to each other -> make referencing, referenced search easier
    def __init__(self, *models: Union[List[Referable], Referable]):
        self._models_key_id: Dict[str, Referable] = {}

        self._top_level_models: Dict[str, List[str]] = {}
        self._models_key_type: Dict[str, List[str]] = {}
        self._referencing_model_ids_key_id: Dict[str, List[str]] = {}

        if models:
            for model in models:
                if not model:
                    continue
                if isinstance(model, list) or isinstance(model, tuple):
                    self.load_models(model)
                else:
                    self.load_model(model)

    @property
    def model_ids(self) -> Set[str]:
        """
        Property to get the ids of all contained models.

        Returns:
            Set[str]: The set of ids.
        """
        return self._models_key_id.keys()

    def get_contained_ids(self) -> Set[str]:
        """
        Method to get all ids of contained models.

        Returns:
            Set[str]: The set of ids.
        """
        return self.model_ids

    def load_models(self, models: List[Referable]) -> None:
        """
        Method to load all models of the data model.

        Args:
            models (List[Referable]): The list of models to load.
        """
        for model in models:
            self.load_model(model)

    def check_different_model_with_same_id_contained(self, model: Referable) -> bool:
        """
        Method to check if a model is already contained in the data model.

        Args:
            model (Referable): The model to check.

        Returns:
            bool: True if the model is already contained, False otherwise.
        """
        if model.id_short in self.model_ids:
            same_id_model = self.get_model(model.id_short)
            if not same_id_model == model:
                return True
        return False

    def load_model(self, top_level_model: Referable) -> None:
        """
        Method to load a model of the data model.

        Args:
            model (Referable): The model to load.
        """
        top_level_model = assure_id_short_attribute(top_level_model)
        if top_level_model.id_short in self.model_ids:
            raise ValueError(
                f"Model with id {top_level_model.id_short} already loaded."
            )
        all_referables = get_all_contained_referables(top_level_model)
        self._load_contained_models(top_level_model, all_referables)
        self._add_top_level_model(top_level_model)
        self._add_references_to_referencing_models_dict(all_referables)

    def _load_contained_models(
        self, top_level_model: Referable, contained_models: List[Referable]
    ) -> None:
        """
        Method to load all contained models of a model.

        Args:
            model (Referable): The model to load the contained models for.
        """
        for contained_model in contained_models:
            if contained_model.id_short in self.model_ids:
                same_id_model = self.get_model(contained_model.id_short)
                if not same_id_model == contained_model:
                    raise ValueError(
                        f"Model with id {contained_model.id_short} already loaded but with different content. Make sure to only load models with unique ids."
                    )
                replace_attribute_with_model(top_level_model, same_id_model)
                continue
            self._add_model(contained_model)

    def _add_references_to_referencing_models_dict(
        self, referables: List[Referable]
    ) -> None:
        """
        Method to add information about referencing model ids of the input model.

        Args:
            model (Referable): The model to add the information for.
        """

        def add_referencing_ids_to_referencing_models_dict(
            referenced_id: str, contained_model_id: str
        ) -> None:
            for referenced_id in referenced_ids:
                if referenced_id not in self._referencing_model_ids_key_id:
                    self._referencing_model_ids_key_id[referenced_id] = []
                if (
                    contained_model_id
                    not in self._referencing_model_ids_key_id[referenced_id]
                ):
                    self._referencing_model_ids_key_id[referenced_id].append(
                        contained_model_id
                    )

        for contained_model in referables:
            referenced_ids = get_referenced_ids_of_model(contained_model)
            referenced_models = get_referable_attributes_of_model(contained_model)
            referenced_ids += [
                referenced_model.id_short for referenced_model in referenced_models
            ]
            add_referencing_ids_to_referencing_models_dict(
                referenced_ids, contained_model.id_short
            )

    def _add_model(self, model: Referable) -> None:
        """
        Method to add a model to the data model.

        Args:
            model (Referable): The model to add.
        """
        if model.id_short in self.model_ids:
            raise ValueError(f"Model with id {model.id_short} already loaded.")
        self._models_key_id[model.id_short] = model
        # underscore_type_name = get_underscore_class_name_from_model(model)
        type_name = model.__class__.__name__.split(".")[-1]
        if not type_name in self._models_key_type:
            self._models_key_type[type_name] = []
        self._models_key_type[type_name].append(model.id_short)

    def _add_top_level_model(self, model: Referable) -> None:
        """
        Method to add a model to the data model.

        Args:
            model (Referable): The model to add.
        """
        type_name = model.__class__.__name__.split(".")[-1]
        underscore_type_name = convert_camel_case_to_underscrore_str(type_name)
        if not underscore_type_name in self._top_level_models:
            self._top_level_models[underscore_type_name] = []
        self._top_level_models[underscore_type_name].append(model.id_short)

    def from_dict(self, data: NESTED_DICT, types: List[Type]) -> None:
        """
        Method to load a data model from a dict.

        Args:
            data (NESTED_DICT): The dict to load the data model from.
        """
        for attribute_name, attribute_value in data.items():
            class_name = convert_under_score_to_camel_case_str(attribute_name)
            for type_ in types:
                if type_.__name__ == class_name:
                    type_for_attribute_values = type_
                    break
            else:
                raise ValueError(f"Type {class_name} not supported.")
            for model_dict in attribute_value:
                model = type_for_attribute_values(**model_dict)
                self.load_model(model)

    def dict(self) -> NESTED_DICT:
        """
        Method to get the dict of the data model.

        Returns:
            NESTED_DICT: The dict of the data model.
        """
        nested_dict = {}
        for attribute_name, attribute_value in self.get_top_level_models().items():
            nested_dict[attribute_name] = [model.dict() for model in attribute_value]
        return nested_dict

    def json(self) -> str:
        """
        Method to get the json of the data model.

        Returns:
            str: The json of the data model.
        """
        nested_dict = {}
        for attribute_name, attribute_value in self.get_top_level_models().items():
            nested_dict[attribute_name] = [model.dict() for model in attribute_value]
        return json.dumps(nested_dict, indent=4, cls=DateTimeEncoder)

    def get_top_level_models(self) -> Dict[str, List[Referable]]:
        """
        Method to get all models of the data model.

        Returns:
            Dict[str, List[Referable]]: The dictionary of models.
        """
        top_level_models = {}
        for top_level_model_name, top_level_model_ids in self._top_level_models.items():
            top_level_models[top_level_model_name] = [
                self.get_model(model_id) for model_id in top_level_model_ids
            ]
        return top_level_models

    def get_models_of_type_name(self, model_type_name: str) -> List[Referable]:
        """
        Method to get all models of a specific type.

        Args:
            model_type (str): The type of the models to get.

        Returns:
            List[Referable]: The list of models of the type.
        """
        if not model_type_name in self._models_key_type:
            raise ValueError(f"Model type {model_type_name} not supported.")
        return [
            self.get_model(model_id)
            for model_id in self._models_key_type[model_type_name]
        ]

    def get_models_of_type(self, model_type: Type[T]) -> List[T]:
        """
        Method to get all models of a specific type.

        Args:
            model_type (str): The type of the models to get.

        Returns:
            List[Referable]: The list of models of the type.
        """
        type_name = model_type.__name__.split(".")[-1]
        return self.get_models_of_type_name(type_name)

    def get_contained_models(self) -> List[Referable]:
        """
        Method to get all models that are contained in the data model.

        Args:
            model_type (str): The type of the models to get.

        Returns:
            List[Referable]: The list of models of the type.
        """
        return list(self._models_key_id.values())

    def get_referencing_models(self, referenced_model: Referable) -> List[Referable]:
        """
        Method to get all models that reference a specific model directly as an attribute or by its id.

        Args:
            model (Referable): The model to get the referencing models for.

        Returns:
            List[Referable]: The list of referencing models of the mode.
        """
        if not referenced_model.id_short in self._referencing_model_ids_key_id:
            return []
        referencing_model_ids = self._referencing_model_ids_key_id[
            referenced_model.id_short
        ]
        return [self.get_model(model_id) for model_id in referencing_model_ids]

    def get_referencing_models_of_type(
        self, referenced_model: Referable, referencing_model_type: Type[T]
    ) -> List[T]:
        """
        Method to get all models that reference a specific model directly as an attribute or by its id.

        Args:
            model (Referable): The model to get the referencing models for.

        Returns:
            List[Referable]: The list of referencing models of the mode.
        """
        if not referenced_model.id_short in self._referencing_model_ids_key_id:
            return []
        referencing_model_ids = self._referencing_model_ids_key_id[
            referenced_model.id_short
        ]
        return [
            self.get_model(model_id)
            for model_id in referencing_model_ids
            if isinstance(self.get_model(model_id), referencing_model_type)
        ]

    def get_model(self, id_short: str) -> Referable:
        """
        Method to get a model by its id.

        Args:
            model_id (str): The id of the model to get.

        Returns:
            Referable: The model.
        """
        if id_short not in self.model_ids:
            return None
        return self._models_key_id[id_short]

    def contains_model(self, id_short: str) -> bool:
        """
        Method to check if a model is contained in the data model.

        Args:
            id_short (str): The id of the model to check.

        Returns:
            bool: True if the model is contained, False otherwise.
        """
        if self.get_model(id_short) is not None:
            return True
        return False


ORIGIN_DATA_MODEL = TypeVar("ORIGIN_DATA_MODEL")
REFERABLE_MODEL = TypeVar("REFERABLE_MODEL", Referable, List[Referable], DataModel)
