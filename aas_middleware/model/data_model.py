from __future__ import annotations

import json
from typing import Dict, List, Literal, Set, Tuple, TypeVar, Union, Any, Type
from datetime import datetime

from pydantic import BaseModel, Field, ValidationError

from aas_middleware.model.core import Identifiable

from aas_middleware.model.reference_finder import ReferenceFinder, ReferenceInfo
from aas_middleware.model.util import (
    convert_under_score_to_camel_case_str,
    convert_camel_case_to_underscrore_str,
    get_id_with_patch,
    get_value_attributes,
    is_identifiable_container,
    models_are_equal,
)

from aas_middleware.model.util import (
    replace_attribute_with_model,
)


NESTED_DICT = Dict[str, Union[Any, "NESTED_DICT"]]
T = TypeVar("T")


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


class DataModel(BaseModel):
    """
    The data model is a container that allows to store all models of a data model and provides methods to access them easily by their id or type.

    Args:
        **data (Dict[str, Any]): The data to load into the data model (used by pydantic).

    Attributes:
        _models_key_id (Dict[str, Identifiable]): The dictionary of models with their id as key.
        _top_level_models (Dict[str, List[str]]): The dictionary of top level models with their type as key.
        _models_key_type (Dict[str, List[str]]): The dictionary of models with their type as key.
        _reference_info_dict_for_referencing (Dict[str, Dict[str, ReferenceInfo]]): The dictionary of reference infos with keys from the referencing model to the referenced model.
        _reference_info_dict_for_referenced (Dict[str, Dict[str, ReferenceInfo]]): The dictionary of reference infos with keys from the referenced model to the referencing model.
    """

    _reference_infos: List[ReferenceInfo] = []
    _models_key_id: Dict[str, Identifiable] = {}
    _top_level_models: Dict[str, List[str]] = {}
    _models_key_type: Dict[str, List[str]] = {}
    _reference_info_dict_for_referencing: Dict[str, Dict[str, ReferenceInfo]] = {}
    _reference_info_dict_for_referenced: Dict[str, Dict[str, ReferenceInfo]] = {}

    def __init__(self, **data: Dict[str, Any]):
        super().__init__(**data)
        try:
            Identifiable.model_validate(self)
            self.add_model(self)
        except ValidationError:
            for attribute_value in get_value_attributes(self).values():
                if is_identifiable_container(attribute_value):
                    self.add(*attribute_value)
                else:
                    self.add(attribute_value)

    @classmethod
    def from_models(
        cls, *models: Tuple[Identifiable], **data: Dict[str, Any]
    ) -> DataModel:
        """
        Method to create a data model from a list of provided models.

        Args:
            models (Tuple[Identifiable]): The models to load into the data model.
            data (Dict[str, Any]): The data to load into the data model.

        Returns:
            DataModel: The data model with loaded models
        """
        data_model = cls(**data)
        data_model.add(*models)
        return data_model
    
    @classmethod
    def from_model_types(cls, *model_types: Tuple[Type[Identifiable]], **data: Dict[str, Any]) -> DataModel:
        """
        Method to create a data model a provided list of model types.

        Args:
            model_types (Tuple[Type[Identifiable]]): The model types to load into the data model.
            data (Dict[str, Any]): The data to load into the data model.

        Returns:
            DataModel: The data model with loaded models
        """
        # TODO: implement function to generate data model from types alone!
        raise NotImplementedError

    @property
    def model_ids(self) -> Set[str]:
        """
        Property to get the ids of all contained models.

        Returns:
            Set[str]: The set of ids.
        """
        return set(str(key) for key in self._models_key_id.keys())

    def get_contained_ids(self) -> Set[str]:
        """
        Method to get all ids of contained models.

        Returns:
            Set[str]: The set of ids.
        """
        return self.model_ids

    def add(self, *models: Identifiable) -> None:
        """
        Method to add models to the data model.

        Args:
            *models (Tuple[Identifiable]): The models to load into the data model.
        """
        for model in models:
            self.add_model(model)

    def add_model(self, model: Identifiable) -> None:
        """
        Method to load a model of the data model.

        Args:
            model (Identifiable): The model to load.
        """
        Identifiable.model_validate(model)
        model_id = get_id_with_patch(model)
        if model_id in self.model_ids:
            raise ValueError(f"Model with id {model_id} already loaded.")
        all_identifiables, reference_infos = ReferenceFinder.find(model)
        self._add_contained_models(model, all_identifiables)
        self._add_top_level_model(model)
        self._add_references_to_referencing_models_dict(reference_infos)

    def check_different_model_with_same_id_contained(self, model: Identifiable) -> bool:
        """
        Method to check if a model is already contained in the data model.

        Args:
            model (Identifiable): The model to check.

        Returns:
            bool: True if the model is already contained, False otherwise.
        """
        model_id = get_id_with_patch(model)
        if model_id in self.model_ids:
            same_id_model = self.get_model(model_id)
            if not same_id_model == model:
                return True
        return False

    def _add_contained_models(
        self, top_level_model: Identifiable, contained_models: List[Identifiable]
    ) -> None:
        """
        Method to load all contained models of a model.

        Args:
            top_level_model (Identifiable): The top level model to load.
            contained_models (List[Identifiable]): The contained models to load.
        """
        for contained_model in contained_models:
            contained_model_id = get_id_with_patch(contained_model)
            if contained_model_id in self.model_ids:
                same_id_model = self.get_model(contained_model_id)
                if not models_are_equal(same_id_model, contained_model):
                    raise ValueError(
                        f"Model with id {contained_model_id} already loaded but with different content. Make sure to only load models with unique ids."
                    )
                replace_attribute_with_model(top_level_model, same_id_model)
                continue
            self._add_model(contained_model)

    def _add_references_to_referencing_models_dict(
        self, reference_infos: List[ReferenceInfo]
    ) -> None:
        """
        Method to add information about referencing model ids of the input model.

        Args:
            model (Identifiable): The model to add the information for.
        """
        # TODO: make sure that the reference_infos are unique -> set and frozen -> update when the attribute is adjusted by replace_attribute_with_model
        self._reference_infos += reference_infos
        for reference_info in reference_infos:
            referencing_model_id = reference_info.identifiable_id
            referenced_model_id = reference_info.reference_id
            if not referencing_model_id in self._reference_info_dict_for_referencing:
                self._reference_info_dict_for_referencing[referencing_model_id] = {}
            self._reference_info_dict_for_referencing[referencing_model_id][
                referenced_model_id
            ] = reference_info
            if not referenced_model_id in self._reference_info_dict_for_referenced:
                self._reference_info_dict_for_referenced[referenced_model_id] = {}
            self._reference_info_dict_for_referenced[referenced_model_id][
                referencing_model_id
            ] = reference_info

    def _add_model(self, model: Identifiable) -> None:
        """
        Method to add a model to the data model.

        Args:
            model (Identifiable): The model to add.
        """
        model_id = get_id_with_patch(model)
        if model_id in self.model_ids:
            raise ValueError(f"Model with id {model_id} already loaded.")
        self._models_key_id[model_id] = model
        type_name = model.__class__.__name__.split(".")[-1]
        if not type_name in self._models_key_type:
            self._models_key_type[type_name] = []
        self._models_key_type[type_name].append(model_id)

    def _add_top_level_model(self, model: Identifiable) -> None:
        """
        Method to add a model to the data model.

        Args:
            model (Identifiable): The model to add.
        """
        type_name = model.__class__.__name__.split(".")[-1]
        underscore_type_name = convert_camel_case_to_underscrore_str(type_name)
        if not underscore_type_name in self._top_level_models:
            self._top_level_models[underscore_type_name] = []
        self._top_level_models[underscore_type_name].append(get_id_with_patch(model))

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
                self.add(model)

    def dict(self) -> NESTED_DICT:
        """
        Method to get the dict of the data model.

        Returns:
            NESTED_DICT: The dict of the data model.
        """
        nested_dict = {}
        for attribute_name, attribute_value in self.get_top_level_models().items():
            nested_dict[attribute_name] = [
                model.model_dump() for model in attribute_value
            ]
        return nested_dict

    def json(self) -> str:
        """
        Method to get the json of the data model.

        Returns:
            str: The json of the data model.
        """
        nested_dict = {}
        for attribute_name, attribute_value in self.get_top_level_models().items():
            # TODO: if a non-BaseModel object is loaded, this breakds down -> adjust this
            nested_dict[attribute_name] = [
                model.model_dump() for model in attribute_value
            ]
        return json.dumps(nested_dict, indent=4, cls=DateTimeEncoder)

    def get_top_level_models(self) -> Dict[str, List[Identifiable]]:
        """
        Method to get all models of the data model.

        Returns:
            Dict[str, List[Identifiable]]: The dictionary of models.
        """
        top_level_models = {}
        for top_level_model_name, top_level_model_ids in self._top_level_models.items():
            top_level_models[top_level_model_name] = [
                self.get_model(model_id) for model_id in top_level_model_ids
            ]
        return top_level_models
    
    def get_top_level_types(self) -> List[Type[Identifiable]]:
        """
        Method to get all types of the top level models in the data model.

        Returns:
            List[Type[Identifiable]]: The types of the top level models in the data model
        """
        # TODO: implement function and change structure in DataModel that it can be instantiated also with types
        # TODO: also add the possibility to specify a name of data model
        # TODO: add the possibility that a DataModel is frozen -> no types can be added or removed.
        raise NotImplementedError

    def get_models_of_type_name(self, model_type_name: str) -> List[Identifiable]:
        """
        Method to get all models of a specific type.

        Args:
            model_type (str): The type of the models to get.

        Returns:
            List[Identifiable]: The list of models of the type.
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
            model_type (Type[T]): The type of the models to get.

        Returns:
            List[T]: The list of models of the type.
        """
        type_name = model_type.__name__.split(".")[-1]
        return self.get_models_of_type_name(type_name)

    def get_contained_models(self) -> List[Identifiable]:
        """
        Method to get all models that are contained in the data model.

        Returns:
            List[Identifiable]: The list of models.
        """
        return list(self._models_key_id.values())

    def get_referencing_info(
        self, referenced_model: Identifiable
    ) -> List[ReferenceInfo]:
        """
        Method to get all reference infos of a model.

        Args:
            referenced_model (Identifiable): The model to get the reference infos for.

        Returns:
            List[ReferenceInfo]: The list of reference infos.
        """
        referenced_model_id = get_id_with_patch(referenced_model)
        if not referenced_model_id in self._reference_info_dict_for_referenced:
            return []
        return list(
            self._reference_info_dict_for_referenced[referenced_model_id].values()
        )

    def get_referencing_models(
        self, referenced_model: Identifiable
    ) -> List[Identifiable]:
        """
        Method to get all models that reference a specific model directly as an attribute or by its id.

        Args:
            referenced_model (Identifiable): The model to get the referencing models for.

        Returns:
            List[Identifiable]: The list of referencing models of the model.
        """
        referenced_model_id = get_id_with_patch(referenced_model)
        if not referenced_model_id in self._reference_info_dict_for_referenced:
            return []
        referencing_model_dict = self._reference_info_dict_for_referenced[
            referenced_model_id
        ]
        return [self.get_model(model_id) for model_id in referencing_model_dict]

    def get_referencing_models_of_type(
        self, referenced_model: Identifiable, referencing_model_type: Type[T]
    ) -> List[T]:
        """
        Method to get all models that reference a specific model directly as an attribute or by its id.

        Args:
            referenced_model (Identifiable): The model to get the referencing models for.
            referencing_model_type (Type[T]): The type of the referencing models to get.

        Returns:
            List[T]: The list of referencing models of the model.
        """
        referenced_model_id = get_id_with_patch(referenced_model)
        if not referenced_model_id in self._reference_info_dict_for_referenced:
            return []
        referencing_model_dict = self._reference_info_dict_for_referenced[
            referenced_model_id
        ]
        return [
            self.get_model(model_id)
            for model_id in referencing_model_dict
            if isinstance(self.get_model(model_id), referencing_model_type)
        ]

    def get_referenced_info(
        self, referencing_model: Identifiable
    ) -> List[ReferenceInfo]:
        """
        Method to get all reference infos of a model.

        Args:
            referencing_model (Identifiable): The model to get the reference infos for.

        Returns:
            List[ReferenceInfo]: The list of reference infos.
        """
        referencing_model_id = get_id_with_patch(referencing_model)
        if not referencing_model_id in self._reference_info_dict_for_referencing:
            return []
        return list(
            self._reference_info_dict_for_referencing[referencing_model_id].values()
        )

    def get_referenced_models(
        self, referencing_model: Identifiable
    ) -> List[Identifiable]:
        """
        Method to get all models that are referenced by a specific model directly as an attribute or by its id.

        Args:
            referencing_model (Identifiable): The model to get the referenced models for.

        Returns:
            List[Identifiable]: The list of referenced models of the model.
        """
        referencing_model_id = get_id_with_patch(referencing_model)
        if not referencing_model_id in self._reference_info_dict_for_referencing:
            return []
        referenced_model_dict = self._reference_info_dict_for_referencing[
            referencing_model_id
        ]
        return [self.get_model(model_id) for model_id in referenced_model_dict]

    def get_referenced_models_of_type(
        self, referencing_model: Identifiable, referenced_model_type: Type[T]
    ) -> List[T]:
        """
        Method to get all models that are referenced by a specific model directly as an attribute or by its id.

        Args:
            referencing_model (Identifiable): The model to get the referenced models for.
            referenced_model_type (Type[T]): The type of the referenced models to get.

        Returns:
            List[T]: The list of referenced models of the model.
        """
        referencing_model_id = get_id_with_patch(referencing_model)
        if not referencing_model_id in self._reference_info_dict_for_referencing:
            return []
        referenced_model_dict = self._reference_info_dict_for_referencing[
            referencing_model_id
        ]
        return [
            self.get_model(model_id)
            for model_id in referenced_model_dict
            if isinstance(self.get_model(model_id), referenced_model_type)
        ]

    def get_model(self, model_id: str) -> Identifiable:
        """
        Method to get a model by its id.

        Args:
            model_id (str): The id of the model to get.

        Returns:
            Identifiable: The model.
        """
        if model_id not in self.model_ids:
            return None
        return self._models_key_id[model_id]

    def contains_model(self, model_id: str) -> bool:
        """
        Method to check if a model is contained in the data model.

        Args:
            model_id (str): The id of the model to check.

        Returns:
            bool: True if the model is contained, False otherwise.
        """
        if self.get_model(model_id) is not None:
            return True
        return False
