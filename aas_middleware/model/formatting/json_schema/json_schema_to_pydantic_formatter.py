from enum import Enum
from typing import List, Protocol, Any
from uuid import UUID

from aas_middleware.model.data_model import DataModel as AasMiddlewareDataModel

# Standard Library
from collections import defaultdict
import json
from types import NoneType
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)
import typing

# Third Party Libraries
from datamodel_code_generator.format import PythonVersion
from datamodel_code_generator.model import DataModel, DataModelFieldBase
from datamodel_code_generator.model import pydantic as pydantic_model
from datamodel_code_generator.parser import DefaultPutDict, LiteralType
from datamodel_code_generator.parser.jsonschema import (
    DEFAULT_FIELD_KEYS,
    JsonSchemaObject,
)
from datamodel_code_generator.parser.jsonschema import (
    JsonSchemaParser,
)
from datamodel_code_generator.types import DataTypeManager, StrictTypes
from pydantic import BaseModel, ConfigDict, Field, create_model

from aas_middleware.model.util import convert_camel_case_to_underscrore_str


class JsonSchemaFormatter:
    """
    Allows to serialize and deserialize DataModels to json schema and vice versa.
    """

    def serialize(self, data: AasMiddlewareDataModel) -> Dict[str, Any]:
        """
        Serialize a DataModel object to a json schema, where all types are defined.

        Args:
            data (DataModel): A data model

        Returns:
            Dict[str, Any]: A dict containing the json schema of the data model.
        """
        top_level_types = data.get_top_level_types()
        return generate_dynamic_schema(top_level_types)

    def deserialize(self, data: Dict[str, Any]) -> AasMiddlewareDataModel:
        """
        Deserialize a json schema to a DataModel object.

        Args:
            data (Dict[str, Any]): A dict containing the json schema of the data model.

        Returns:
            DataModel: A data model that holds the objects that were deserialized
        """
        dynamic_type = jsonschema_to_pydantic(data)
        # test if all attributes are called like the class and if all are lists, if so create a DataModel from the types
        if all(
            attribute_name == convert_camel_case_to_underscrore_str(typing.get_args(field_info.annotation)[0].__name__) and typing.get_origin(field_info.annotation) == list
            for attribute_name, field_info in dynamic_type.model_fields.items()
        ):
            all_types = [typing.get_args(field_info.annotation)[0] for field_info in dynamic_type.model_fields.values()]
            return AasMiddlewareDataModel.from_model_types(*all_types)
        return AasMiddlewareDataModel.from_model_types(dynamic_type)


def generate_dynamic_schema(
    models: list[Type[BaseModel]]
) -> dict[str, Any]:
    # Define fields for the new DataModel, each as a List of the provided model type
    fields = {
        convert_camel_case_to_underscrore_str(model.__name__): (list[model], None)
        for model in models
    }

    # Dynamically create a new DataModel with the specified fields
    dynamic_datamodel_for_schema: type[BaseModel] = create_model(
        f"DataModel", **fields
    )

    # Generate and return the JSON schema for the dynamically created DataModel
    return dynamic_datamodel_for_schema.model_json_schema()


ORIGIN_TYPES = {
    "Annotated": typing.Annotated,
    "Optional": Optional,
    "List": list,
    "Dict": dict,
    "Set": set,
    "FrozenSet": frozenset,
    "Tuple": tuple,
    "Union": Union,
    "Any": Any,
    "Literal": Literal,
    "UUID": UUID,
    "Field": Field
}


class JsonSchemaToPydanticParser(JsonSchemaParser):
    def __init__(
        self,
        source: JsonSchemaObject,
        data_model_type: Type[DataModel] = pydantic_model.BaseModel,
        data_model_root_type: Type[DataModel] = pydantic_model.CustomRootType,
        data_type_manager_type: Type[DataTypeManager] = pydantic_model.DataTypeManager,
        data_model_field_type: Type[DataModelFieldBase] = pydantic_model.DataModelField,
        base_class: Optional[str] = None,
        extra_template_data: Optional[DefaultDict[str, Dict[str, Any]]] = None,
        target_python_version: PythonVersion = PythonVersion.PY_37,
        dump_resolve_reference_action: Optional[Callable[[Iterable[str]], str]] = None,
        validation: bool = False,
        field_constraints: bool = False,
        snake_case_field: bool = False,
        strip_default_none: bool = False,
        aliases: Optional[Mapping[str, str]] = None,
        allow_population_by_field_name: bool = False,
        apply_default_values_for_required_fields: bool = False,
        force_optional_for_required_fields: bool = False,
        class_name: Optional[str] = None,
        use_standard_collections: bool = False,
        use_schema_description: bool = False,
        reuse_model: bool = False,
        encoding: str = "utf-8",
        enum_field_as_literal: Optional[LiteralType] = None,
        set_default_enum_member: bool = False,
        strict_nullable: bool = False,
        use_generic_container_types: bool = False,
        enable_faux_immutability: bool = False,
        remote_text_cache: Optional[DefaultPutDict[str, str]] = None,
        disable_appending_item_suffix: bool = False,
        strict_types: Optional[Sequence[StrictTypes]] = None,
        empty_enum_field_name: Optional[str] = None,
        custom_class_name_generator: Optional[Callable[[str], str]] = None,
        field_extra_keys: Optional[Set[str]] = None,
        field_include_all_keys: bool = False,
        wrap_string_literal: Optional[bool] = None,
        use_title_as_name: bool = False,
        http_headers: Optional[Sequence[Tuple[str, str]]] = None,
        http_ignore_tls: bool = False,
        use_annotated: bool = False,
        use_non_positive_negative_number_constrained_types: bool = False,
    ):
        _source = json.dumps(source)
        super().__init__(
            source=_source,
            data_model_type=data_model_type,
            data_model_root_type=data_model_root_type,
            data_type_manager_type=data_type_manager_type,
            data_model_field_type=data_model_field_type,
            base_class=base_class,
            custom_template_dir=None,
            extra_template_data=extra_template_data,
            target_python_version=target_python_version,
            dump_resolve_reference_action=dump_resolve_reference_action,
            validation=validation,
            field_constraints=field_constraints,
            snake_case_field=snake_case_field,
            strip_default_none=strip_default_none,
            aliases=aliases,
            allow_population_by_field_name=allow_population_by_field_name,
            apply_default_values_for_required_fields=apply_default_values_for_required_fields,
            force_optional_for_required_fields=force_optional_for_required_fields,
            class_name=class_name,
            use_standard_collections=use_standard_collections,
            base_path=None,
            use_schema_description=use_schema_description,
            reuse_model=reuse_model,
            encoding=encoding,
            enum_field_as_literal=enum_field_as_literal,
            set_default_enum_member=set_default_enum_member,
            strict_nullable=strict_nullable,
            use_generic_container_types=use_generic_container_types,
            enable_faux_immutability=enable_faux_immutability,
            remote_text_cache=remote_text_cache,
            disable_appending_item_suffix=disable_appending_item_suffix,
            strict_types=strict_types,
            empty_enum_field_name=empty_enum_field_name,
            custom_class_name_generator=custom_class_name_generator,
            field_extra_keys=field_extra_keys,
            field_include_all_keys=field_include_all_keys,
            wrap_string_literal=wrap_string_literal,
            use_title_as_name=use_title_as_name,
            http_headers=http_headers,
            http_ignore_tls=http_ignore_tls,
            use_annotated=use_annotated,
            use_non_positive_negative_number_constrained_types=use_non_positive_negative_number_constrained_types,
        )

        self.remote_object_cache: DefaultPutDict[str, Dict[str, Any]] = DefaultPutDict()
        self.raw_obj: Dict[Any, Any] = {}
        self._root_id: Optional[str] = None
        self._root_id_base_path: Optional[str] = None
        self.reserved_refs: DefaultDict[Tuple[str], Set[str]] = defaultdict(set)
        self.field_keys: Set[str] = {*DEFAULT_FIELD_KEYS, *self.field_extra_keys}


# define a class config to use for create_model
class JsonSchemaConfig(ConfigDict):
    populate_by_name = True
    validate_assignment = True
    validate_default = True
    from_attributes = True


def jsonschema_to_pydantic(
    schema: dict[str, str],
    *,
    config: Type = JsonSchemaConfig,
) -> Type[BaseModel]:
    parser = JsonSchemaToPydanticParser(
        source=schema,
        validation=True,
        field_constraints=True,
        snake_case_field=True,
        strip_default_none=True,
        allow_population_by_field_name=True,
        use_schema_description=True,
        strict_nullable=True,
        use_title_as_name=True,
        use_non_positive_negative_number_constrained_types=True,
        apply_default_values_for_required_fields=False,
        use_annotated=True,
    )
    parser.parse()
    results: list[DataModel] = parser.results

    # sort results depending on their refenced classes
    results.sort(key=lambda x: len(x.reference_classes))

    # sort the results that they don't have a reference to a class that is after them
    copied_results = [*results]

    sorted_results: list[DataModel] = []
    while copied_results:
        for result in copied_results:
            if not result.reference_classes:
                sorted_results.append(result)
                copied_results.remove(result)
                continue
            if all(
                any(
                    True
                    for already_sorted_result in sorted_results
                    if ref.split("/")[-1] == already_sorted_result.name or ref.split("/")[-1].split("#")[0] == convert_camel_case_to_underscrore_str(already_sorted_result.name)
                )
                for ref in result.reference_classes
            ):
                sorted_results.append(result)
                copied_results.remove(result)
                continue

    dynamic_models = {}

    for sorted_result in sorted_results:
        fields = {}
        if sorted_result.base_class == "Enum" and "#-datamodel-code-generator-#-enum-#-special-#" in sorted_result.path:
            dynamic_models.update(
                {
                    sorted_result.name: typing.Literal[
                        tuple(attr.name for attr in sorted_result.fields)
                    ]
                }
            )
            continue
        if sorted_result.base_class == "Enum":
            dynamic_models.update(
                {
                    sorted_result.name: Enum(
                        sorted_result.name,
                        {attr.name: attr.name for attr in sorted_result.fields},
                    )
                }
            )
            continue
        for attr in sorted_result.fields:
            if attr.annotated is not None and "unique_items" in attr.annotated:
                assert attr.type_hint[:4] == "List", f"unique_items only allowed for List types, got {attr.type_hint}"
                inner_type_hint = attr.type_hint[5:-1]
                str_type_hint = f"Set[{inner_type_hint}]"
            elif attr.annotated is not None and ("max_items" in attr.annotated or "min_items" in attr.annotated):
                # TODO: if datamodel-code-generator supports correct tuple transformation, update this to correctly consider the inner type hint
                str_type_hint = "Tuple[Any, ...]"
                # str_type_hint = attr.annotated.replace(
                #     "max_items", "max_length"
                # ).replace("min_items", "min_length")
            else:
                str_type_hint = attr.annotated if attr.annotated is not None else attr.type_hint
            if str_type_hint is None:
                type_hint = NoneType
            else:
                type_hint = eval(str_type_hint, ORIGIN_TYPES, dynamic_models)
            fields[attr.name] = (type_hint, ... if attr.required else attr.default)
        dynamic_models.update(
            {
                sorted_result.name: create_model(
                    sorted_result.name, __config__=config, **fields
                )
            }
        )
    return dynamic_models[schema["title"]]
