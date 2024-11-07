# Standard Library
from collections import defaultdict
import json
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
)

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
    JsonSchemaParser as BaseJsonSchemaParser,
)
from datamodel_code_generator.types import DataTypeManager, StrictTypes

from pydantic import BaseModel, ConfigDict, create_model


# extend the data-model json-schema-parser to accept a source of a JsonSchemaObject
# remove template options from the init methods and default them to none in the super() call
class JsonSchemaParser(BaseJsonSchemaParser):
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
        super().__init__(
            source=source,
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

    # remove path from the required options
    def parse_obj(self, name: str, obj: JsonSchemaObject) -> None:
        if obj.is_array:  # noqa: WPS223
            self.parse_array(name, obj, [])
        elif obj.allOf:
            self.parse_all_of(name, obj, [])
        elif obj.oneOf:
            self.parse_root_type(name, obj, [])
        elif obj.is_object:
            self.parse_object(name, obj, [])
        elif obj.enum:
            self.parse_enum(name, obj, [])
        else:
            self.parse_root_type(name, obj, [])
        self.parse_ref(obj, [])


# define a class config to use for create_model
class JsonSchemaConfig(ConfigDict):
    populate_by_name = True
    validate_assignment = True
    validate_default = True
    from_attributes = True


def jsonschema_to_pydantic(
    schema: JsonSchemaObject,
    *,
    config: Type = JsonSchemaConfig,
) -> Type[BaseModel]:
    parser = JsonSchemaParser(
        source=None,
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
    parser.parse_obj(schema.title, obj=schema)
    print(len(parser.results))
    result: DataModel = parser.results[0]
    # this is added for my use case.  I excluded some fields from the generated model based on an indicator column
    fields_to_exclude = [
        attr
        for attr in schema.properties
        if schema.properties[attr].extras.get(
            "an_extra_column_use_to_indicate_exclude", None
        )
    ]

    fields = {}
    for attr in result.fields:
        if attr.name not in fields_to_exclude:
            fields[attr.name] = (attr.type_hint, ... if attr.required else attr.default)
            if attr.unresolved_types:
                # FIXME: create a model for the unresolved types....
                print("Unresolved types found", attr.unresolved_types)

    return create_model(schema.title, __config__=config, **fields)


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

    # with open("ProvisionofSimulationModelsAAS_schema.json", "r") as f:
    #     parsed_json_obj = json.loads(f.read())
    with open("RecreatedSchema.json", "r") as f:
        parsed_json_obj = json.loads(f.read())

    # json.loads may be required.  In my case I had been using Json type in pydantic/sqlalchemy
    PydanticModel = jsonschema_to_pydantic(
        schema=JsonSchemaObject.model_validate(parsed_json_obj),
    )
    # PydanticModel.model_rebuild(_parent_namespace_depth=6)

    assert parsed_json_obj == PydanticModel.model_json_schema()
    with open("RecreatedSchema.json", "w") as f:
        f.write(json.dumps(PydanticModel.model_json_schema(), indent=4))
    print(PydanticModel.model_fields)
