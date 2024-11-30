from __future__ import annotations
from enum import Enum
import enum
import threading
import time
from typing import Any, List, Literal, Optional, Set, Tuple, Type, Union

import anyio
from fastapi.testclient import TestClient
from fastapi import FastAPI

from pydantic import BaseModel
import pytest
import uvicorn

from aas_middleware.middleware.aas_persistence_middleware import AasMiddleware
from aas_middleware.model.core import Identifier, Reference

from aas_middleware.model.data_model import DataModel
from aas_middleware.model.formatting.aas.aas_model import (
    AAS,
    Submodel,
    SubmodelElementCollection,
)

from aas_middleware.middleware.middleware import Middleware

class ExampleEnum(str, Enum):
    value1 = "value1"
    value2 = "value2"

# TODO: also add optional attribute!

class SimpleExampleSEC(SubmodelElementCollection):
    integer_attribute: int
    string_attribute: str
    float_attribute: float
    literal_attribute: Literal["value1", "value2"]
    enum_attribute: ExampleEnum
    list_attribute: List[str]
    tuple_attribute: Tuple[str, str]
    set_attribute: Set[str]
    union_attribute: Union[str, int]


class ExampleSEC(SubmodelElementCollection):
    integer_attribute: int
    string_attribute: str
    float_attribute: float
    literal_attribute: Literal["value1", "value2"]
    enum_attribute: ExampleEnum
    list_attribute: List[str]
    tuple_attribute: Tuple[str, str]
    set_attribute: Set[str]
    union_attribute: Union[str, int]
    submodel_element_collection_attribute: SimpleExampleSEC


class ExampleSubmodel(Submodel):
    integer_attribute: int
    string_attribute: str
    float_attribute: float
    literal_attribute: Literal["value1", "value2"]
    enum_attribute: ExampleEnum
    list_attribute: List[str]
    tuple_attribute: Tuple[str, str]
    set_attribute: Set[str]
    union_attribute: Union[str, int]
    submodel_element_collection_attribute_simple: SimpleExampleSEC
    submodel_element_collection_attribute: ExampleSEC
    union_submodel_element_collection_attribute: Union[ExampleSEC, SimpleExampleSEC]
    list_submodel_element_collection_attribute: List[SimpleExampleSEC]


class ExampleSubmodel2(Submodel):
    integer_attribute: int
    string_attribute: str
    float_attribute: float
    literal_attribute: Literal["value1", "value2"]
    enum_attribute: ExampleEnum
    list_attribute: List[str]
    tuple_attribute: Tuple[str, str]
    set_attribute: Set[str]
    union_attribute: Union[str, int]
    submodel_element_collection_attribute_simple: SimpleExampleSEC
    submodel_element_collection_attribute: ExampleSEC
    union_submodel_element_collection_attribute: Union[ExampleSEC, SimpleExampleSEC]
    list_submodel_element_collection_attribute: List[SimpleExampleSEC]


class ExampleSubmodelWithReference(Submodel):
    single_reference: Reference
    list_references: List[Reference]
    tuple_references: Tuple[Reference, Reference]
    set_references: Set[Reference]


class ExampleSubmodelWithIdReference(Submodel):
    referenced_aas_id: str
    referenced_aas_ids: List[str]
    referenced_aas_tuple_ids: Tuple[str, str]
    referenced_aas_set_ids: Set[str]


class ExampleBasemodelWithAssociation(BaseModel):
    id_short: str
    aas_reference: ValidAAS
    aas_list_reference: List[ValidAAS]
    aas_tuple_reference: Tuple[ValidAAS, ValidAAS]


class ExampleBaseMdelWithId(BaseModel):
    id: str
    integer_attribute: int
    string_attribute: str
    float_attribute: float
    literal_attribute: Literal["value1", "value2"]
    enum_attribute: ExampleEnum
    list_attribute: List[str]
    tuple_attribute: Tuple[str, str]
    set_attribute: Set[str]
    union_attribute: Union[str, int]


class ObjectBomWithId:
    def __init__(
        self,
        id: str,
        integer_attribute: int,
        string_attribute: str,
        float_attribute: float,
        literal_attribute: Literal["value1", "value2"],
        enum_attribute: ExampleEnum,
        list_attribute: List[str],
        tuple_attribute: Tuple[str, str],
        set_attribute: Set[str],
        union_attribute: Union[str, int],
    ):
        self.id = id
        self.integer_attribute = integer_attribute
        self.string_attribute = string_attribute
        self.float_attribute = float_attribute
        self.literal_attribute = literal_attribute
        self.enum_attribute = enum_attribute
        self.list_attribute = list_attribute
        self.tuple_attribute = tuple_attribute
        self.set_attribute = set_attribute
        self.union_attribute = union_attribute


class BaseModelWithIdentifierAttribute(BaseModel):
    other_name_id_attribute: Identifier
    id: str


class ObjectWithIdentifierAttribute:
    def __init__(
        self,
        other_name_id_attribute: Identifier,
        id: str,
    ):
        self.other_name_id_attribute = other_name_id_attribute
        self.id = id


class ValidAAS(AAS):
    example_submodel: ExampleSubmodel
    example_submodel_2: ExampleSubmodel2
    union_submodel: Union[ExampleSubmodel, ExampleSubmodel2]
    optional_submodel: Optional[ExampleSubmodel]


class FaultyAas(AAS):
    example_string_value: str


@pytest.fixture(scope="function")
def faulty_aas() -> Type[FaultyAas]:
    return FaultyAas


@pytest.fixture(scope="function")
def simple_submodel_element_collection() -> SubmodelElementCollection:
    return SimpleExampleSEC(
        id_short="simple_submodel_element_collection_id",
        integer_attribute=1,
        string_attribute="string",
        float_attribute=1.1,
        literal_attribute="value1",
        enum_attribute=ExampleEnum.value1,
        list_attribute=["string1", "string2"],
        tuple_attribute=("string1", "string2"),
        set_attribute={"string1", "string2"},
        union_attribute="string",
    )


@pytest.fixture(scope="function")
def example_submodel_element_collection(simple_submodel_element_collection: SubmodelElementCollection) -> SubmodelElementCollection:
    return ExampleSEC(
        id_short="example_submodel_element_collection_id",
        integer_attribute=1,
        string_attribute="string",
        float_attribute=1.1,
        literal_attribute="value1",
        enum_attribute=ExampleEnum.value1,
        list_attribute=["string1", "string2"],
        tuple_attribute=("string1", "string2"),
        set_attribute={"string1", "string2"},
        union_attribute="string",
        submodel_element_collection_attribute=simple_submodel_element_collection,
    )

@pytest.fixture(scope="function")
def example_submodel_element_collection_for_union(simple_submodel_element_collection: SubmodelElementCollection) -> SubmodelElementCollection:
    return ExampleSEC(
        id_short="example_submodel_element_collection_for_union_id",
        integer_attribute=1,
        string_attribute="string",
        float_attribute=1.1,
        literal_attribute="value1",
        enum_attribute=ExampleEnum.value1,
        list_attribute=["string1", "string2"],
        tuple_attribute=("string1", "string2"),
        set_attribute={"string1", "string2"},
        union_attribute="string",
        submodel_element_collection_attribute=simple_submodel_element_collection,
    )


@pytest.fixture(scope="function")
def example_list_submodel_element_collection(simple_submodel_element_collection: SubmodelElementCollection) -> List[SubmodelElementCollection]:
    return [simple_submodel_element_collection]


@pytest.fixture(scope="function")
def example_submodel(simple_submodel_element_collection: SubmodelElementCollection, example_submodel_element_collection: SubmodelElementCollection, example_submodel_element_collection_for_union: SubmodelElementCollection, example_list_submodel_element_collection: List[SubmodelElementCollection]) -> Submodel:
    return ExampleSubmodel(
        id_short="example_submodel_id",
        description="Example Submodel",
        integer_attribute=1,
        string_attribute="string",
        float_attribute=1.1,
        literal_attribute="value1",
        enum_attribute=ExampleEnum.value1,
        list_attribute=["string1_list", "string2_list"],
        tuple_attribute=("string1_tuple", "string2_tuple"),
        set_attribute={"string1_set", "string2_set"},
        union_attribute="string",
        submodel_element_collection_attribute_simple=simple_submodel_element_collection,
        submodel_element_collection_attribute=example_submodel_element_collection,
        union_submodel_element_collection_attribute=example_submodel_element_collection_for_union,
        list_submodel_element_collection_attribute=example_list_submodel_element_collection,
    )

@pytest.fixture(scope="function")
def example_submodel_2(simple_submodel_element_collection: SubmodelElementCollection, example_submodel_element_collection: SubmodelElementCollection, example_submodel_element_collection_for_union: SubmodelElementCollection, example_list_submodel_element_collection: List[SubmodelElementCollection]) -> Submodel:
    return ExampleSubmodel2(
        id_short="example_submodel_2_id",
        integer_attribute=1,
        string_attribute="string",
        float_attribute=1.1,
        literal_attribute="value1",
        enum_attribute=ExampleEnum.value1,
        list_attribute=["string1", "string2"],
        tuple_attribute=("string1", "string2"),
        set_attribute={"string1", "string2"},
        union_attribute="string",
        submodel_element_collection_attribute_simple=simple_submodel_element_collection,
        submodel_element_collection_attribute=example_submodel_element_collection,
        union_submodel_element_collection_attribute=example_submodel_element_collection_for_union,
        list_submodel_element_collection_attribute=example_list_submodel_element_collection,
    )

@pytest.fixture(scope="function")
def example_submodel_for_union(simple_submodel_element_collection: SubmodelElementCollection, example_submodel_element_collection: SubmodelElementCollection, example_submodel_element_collection_for_union: SubmodelElementCollection, example_list_submodel_element_collection: List[SubmodelElementCollection]) -> Submodel:
    return ExampleSubmodel(
        id_short="example_submodel_for_union_id",
        integer_attribute=1,
        string_attribute="string",
        float_attribute=1.1,
        literal_attribute="value1",
        enum_attribute=ExampleEnum.value1,
        list_attribute=["string1_list", "string2_list"],
        tuple_attribute=("string1_tuple", "string2_tuple"),
        set_attribute={"string1_set", "string2_set"},
        union_attribute="string",
        submodel_element_collection_attribute_simple=simple_submodel_element_collection,
        submodel_element_collection_attribute=example_submodel_element_collection,
        union_submodel_element_collection_attribute=example_submodel_element_collection_for_union,
        list_submodel_element_collection_attribute=example_list_submodel_element_collection,
    )

@pytest.fixture(scope="function")
def example_optional_submodel(simple_submodel_element_collection: SubmodelElementCollection, example_submodel_element_collection: SubmodelElementCollection, example_submodel_element_collection_for_union: SubmodelElementCollection, example_list_submodel_element_collection: List[SubmodelElementCollection]) -> Submodel:
    return ExampleSubmodel(
        id_short="example_optional_submodel_id",
        integer_attribute=1,
        string_attribute="string",
        float_attribute=1.1,
        literal_attribute="value1",
        enum_attribute=ExampleEnum.value1,
        list_attribute=["string1_list", "string2_list"],
        tuple_attribute=("string1_tuple", "string2_tuple"),
        set_attribute={"string1_set", "string2_set"},
        union_attribute="string",
        submodel_element_collection_attribute_simple=simple_submodel_element_collection,
        submodel_element_collection_attribute=example_submodel_element_collection,
        union_submodel_element_collection_attribute=example_submodel_element_collection_for_union,
        list_submodel_element_collection_attribute=example_list_submodel_element_collection,
    )


@pytest.fixture(scope="function")
def example_submodel_with_reference() -> ExampleSubmodelWithReference:
    return ExampleSubmodelWithReference(
        id_short="example_submodel_with_reference_components_id",
        single_reference="referenced_aas_1_id",
        list_references=["referenced_aas_1_id", "referenced_aas_2_id"],
        tuple_references=("referenced_aas_1_id", "referenced_aas_2_id"),
        set_references={"referenced_aas_1_id", "referenced_aas_2_id"},
    )


@pytest.fixture(scope="function")
def example_submodel_with_id_reference() -> ExampleSubmodelWithIdReference:
    return ExampleSubmodelWithIdReference(
        id_short="example_submodel_with_id_reference_components_id",
        referenced_aas_id="referenced_aas_1_id",
        referenced_aas_ids=["referenced_aas_1_id", "referenced_aas_2_id"],
        referenced_aas_tuple_ids=("referenced_aas_1_id", "referenced_aas_2_id"),
        referenced_aas_set_ids={"referenced_aas_1_id", "referenced_aas_2_id"},
    )


@pytest.fixture(scope="function")
def example_submodel_with_product_association(
    referenced_aas_1: ValidAAS, referenced_aas_2: ValidAAS
) -> ExampleBasemodelWithAssociation:
    return ExampleBasemodelWithAssociation(
        id_short="example_submodel_with_product_association_id",
        aas_reference=referenced_aas_1,
        aas_list_reference=[referenced_aas_1, referenced_aas_2],
        aas_tuple_reference=(referenced_aas_1, referenced_aas_2),
    )


@pytest.fixture(scope="function")
def example_aas(example_submodel: ExampleSubmodel, example_submodel_2: ExampleSubmodel2, example_submodel_for_union: ExampleSubmodel, example_optional_submodel: ExampleSubmodel) -> AAS:
    return ValidAAS(
        id_short="valid_aas_id",
        example_submodel=example_submodel,
        example_submodel_2=example_submodel_2,
        union_submodel=example_submodel_for_union,
        optional_submodel=example_optional_submodel,
    )


@pytest.fixture(scope="function")
def referenced_aas_1(example_submodel: ExampleSubmodel, example_submodel_2: ExampleSubmodel2, example_submodel_for_union: ExampleSubmodel, example_optional_submodel: ExampleSubmodel) -> AAS:
    return ValidAAS(
        id_short="referenced_aas_1_id",
        example_submodel=example_submodel,
        example_submodel_2=example_submodel_2,
        union_submodel=example_submodel_for_union, 
        optional_submodel=example_optional_submodel,       
    )


@pytest.fixture(scope="function")
def referenced_aas_2(example_submodel: ExampleSubmodel, example_submodel_2: ExampleSubmodel2, example_submodel_for_union: ExampleSubmodel, example_optional_submodel: ExampleSubmodel) -> AAS:
    return ValidAAS(
        id_short="referenced_aas_2_id",
        example_submodel=example_submodel,
        example_submodel_2=example_submodel_2,
        union_submodel=example_submodel_for_union,
        optional_submodel=example_optional_submodel,
    )


@pytest.fixture(scope="function")
def example_basemodel_with_id() -> ExampleBaseMdelWithId:
    return ExampleBaseMdelWithId(
        id="example_basemodel_with_id",
        integer_attribute=1,
        string_attribute="string",
        float_attribute=1.1,
        literal_attribute="value1",
        enum_attribute=ExampleEnum.value1,
        list_attribute=["string1", "string2"],
        tuple_attribute=("string1", "string2"),
        set_attribute={"string1", "string2"},
        union_attribute="string",
    )


@pytest.fixture(scope="function")
def example_object_with_id() -> ObjectBomWithId:
    return ObjectBomWithId(
        id="example_object_with_id", 
        integer_attribute=1,
        string_attribute="string",
        float_attribute=1.1,
        literal_attribute="value1",
        enum_attribute=ExampleEnum.value1,
        list_attribute=["string1", "string2"],
        tuple_attribute=("string1", "string2"),
        set_attribute={"string1", "string2"},
        union_attribute="string",
    )


@pytest.fixture(scope="function")
def example_basemodel_with_identifier_attribute() -> (
    BaseModelWithIdentifierAttribute
):
    return BaseModelWithIdentifierAttribute(
        other_name_id_attribute="example_basemodel_with_identifier_attribute_id",
        id="id_named_attribute",
    )


@pytest.fixture(scope="function")
def example_object_with_identifier_attribute() -> ObjectWithIdentifierAttribute:
    return ObjectWithIdentifierAttribute(
        other_name_id_attribute="example_object_with_identifier_attribute_id",
        id="id_named_attribute",
    )

AAS_SERVER_ADDRESS = "localhost"
AAS_SERVER_PORT = 8081
SUBMODEL_SERVER_ADDRESS = "localhost"
SUBMODEL_SERVER_PORT = 8081

@pytest.fixture(scope="function")
def example_middleware(example_aas: ValidAAS, example_submodel: ExampleSubmodel) -> Middleware:
    data_model = DataModel.from_models(example_aas)

    middleware  = AasMiddleware()
    middleware.load_aas_persistent_data_model("test", data_model, AAS_SERVER_ADDRESS, AAS_SERVER_PORT, SUBMODEL_SERVER_ADDRESS, SUBMODEL_SERVER_PORT)
    middleware.generate_rest_api_for_data_model("test")

    trivial_float_connector = TrivialFloatConnector()
    middleware.add_connector("test_connector", trivial_float_connector, model_type=float)
    
    trivial_float_connector_2 = TrivialFloatConnector()
    middleware.add_connector(
        "test_connected_connector",
        trivial_float_connector_2,
        model_type=float,
        data_model_name="test",
        model_id="valid_aas_id",
        contained_model_id="example_submodel_id",
        field_id="float_attribute",
    )


    @middleware.workflow()
    async def example_workflow() -> bool:
        await anyio.sleep(2)
        return True
    
    @middleware.workflow()
    def sync_example_workflow() -> bool:
        time.sleep(2)
        return True
    
    async def exception_workflow() -> bool:
        raise Exception("Error")
    
    @middleware.workflow(interval=1)
    async def example_workflow_interval() -> bool:
        return True
    
    @middleware.workflow(on_startup=True)
    async def example_workflow_startup() -> bool:
        return True
    
    @middleware.workflow()
    async def example_workflow_with_primitive_argument(arg1: int) -> int:
        return arg1
    
    @middleware.workflow()
    async def example_workflow_with_complex_argument(arg1: ExampleSubmodel) -> ExampleSubmodel:
        return arg1
    
    @middleware.workflow()
    async def example_workflow_with_multiple_arguments(arg1: ExampleSubmodel, arg2: int) -> ExampleSubmodel:
        arg1.integer_attribute = arg2
        return arg1
    
    @middleware.workflow(arg2=3)
    async def example_workflow_with_default_argument(arg1: ExampleSubmodel, arg2: int) -> ExampleSubmodel:
        arg1.integer_attribute = arg2
        return arg1
    
    @middleware.workflow(arg1=example_submodel)
    async def example_workflow_with_default_argument_complex(arg1: ExampleSubmodel, arg2: int) -> ExampleSubmodel:
        arg1.integer_attribute = arg2
        return arg1
    
    @middleware.workflow(blocking=True)
    async def example_workflow_blocking() -> bool:
        anyio.sleep(1)
        return True
    
    @middleware.workflow(blocking=True, pool_size=3)
    async def example_workflow_blocking_pool_size() -> bool:
        anyio.sleep(1)
        return True
    
    @middleware.workflow(queueing=True)
    async def example_workflow_queuing() -> bool:
        anyio.sleep(1)
        return True
    
    @middleware.workflow(queueing=True, pool_size=3)
    async def example_workflow_queuing_pool_size() -> bool:
        anyio.sleep(1)
        return True

    
    return middleware


@pytest.fixture(scope="function")
def client(
    example_middleware: Middleware
) -> TestClient:
    """
    Create a new FastAPI TestClient based on the current app.
    """
    with TestClient(example_middleware.app) as client:
        return client
    
class TrivialFloatConnector:
    def __init__(self):
        pass

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, body: float) -> None:
        print(body)
        pass

    async def provide(self) -> Any:
        return 1.0
    


