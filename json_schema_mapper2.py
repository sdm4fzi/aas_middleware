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
from pydantic import BaseModel, ConfigDict, create_model

from aas_middleware.model.formatting.util import compare_schemas


ORIGIN_TYPES = {
    "Optional": Optional,
    "List": list,
    "Dict": dict,
    "Set": set,
    "FrozenSet": frozenset,
    "Tuple": tuple,
    "Union": Union,
    "Any": Any,
    "Literal": Literal
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
            if all(any(True for result in sorted_results if ref.split("/")[-1] == result.name) for ref in result.reference_classes):
                sorted_results.append(result)
                copied_results.remove(result)
                continue


    pydantic_models = {}

    for sorted_result in sorted_results:
        fields = {}
        for attr in sorted_result.fields:
            type_hint = eval(attr.type_hint, ORIGIN_TYPES, pydantic_models)
            if type_hint is None:
                type_hint = NoneType
            fields[attr.name] = (type_hint, ... if attr.required else attr.default)
        pydantic_models.update({
            sorted_result.name: create_model(sorted_result.name, __config__=config, **fields)
        })
    return pydantic_models[schema["title"]]


if __name__ == "__main__":
    # class MoreNestedModel(BaseModel):
    #     id: int
    #     full_name: str

    # class OtherModel(BaseModel):
    #     id: int
    #     name: str
    #     more_nested: MoreNestedModel

    # class ExampleModel(BaseModel):
    #     id: int
    #     name: str
    #     other_model: OtherModel

    # parsed_json_obj = ExampleModel.model_json_schema()

    with open("ProvisionofSimulationModelsAAS_schema.json", "r") as f:
        parsed_json_obj = json.loads(f.read())
    # with open("RecreatedSchema.json", "r") as f:
    #     parsed_json_obj = json.loads(f.read())
    PydanticModel = jsonschema_to_pydantic(
        schema=parsed_json_obj,
    )
    with open("RecreatedSchema.json", "w") as f:
        f.write(json.dumps(PydanticModel.model_json_schema(), indent=4))
    assert compare_schemas(parsed_json_obj, PydanticModel.model_json_schema())

    print(PydanticModel.model_fields)
