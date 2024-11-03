from types import NoneType
import typing

from pydantic import BaseModel

from graphene_pydantic import PydanticObjectType
from graphene_pydantic.registry import get_global_registry

import graphene
from aas_middleware.connect.connectors.connector import Connector

if typing.TYPE_CHECKING:
    from aas_middleware.middleware.middleware import Middleware
from aas_middleware.middleware.registries import ConnectionInfo
from aas_middleware.model.data_model import DataModel
from starlette_graphene3 import (
    GraphQLApp,
    make_graphiql_handler,
)

from aas_middleware.model.formatting.aas.aas_middleware_util import get_all_submodel_elements_from_submodel, get_contained_models_attribute_info, is_basemodel_union_type, is_optional_basemodel_type
from aas_middleware.model.formatting.aas.aas_model import AAS, Blob, File, Submodel, SubmodelElementCollection

def get_base_query_and_mutation_classes() -> (
    typing.Tuple[graphene.ObjectType, graphene.ObjectType]
):
    """
    Returns the base query and mutation classes for the GraphQL endpoint.

    Returns:
        tuple: Tuple of the base query and mutation classes for the GraphQL endpoint.
    """

    class Query(graphene.ObjectType):
        pass

    class Mutation(graphene.ObjectType):
        pass

    return Query, Mutation

class GraphQLRouter:
    def  __init__(self, data_model: DataModel, data_model_name: str, middleware: "Middleware"):
        self.data_model = data_model
        self.data_model_name = data_model_name

        self.middleware = middleware
        self.query, self.mutation = get_base_query_and_mutation_classes()

    def get_connector(self, item_id: str) -> Connector:
        return self.middleware.persistence_registry.get_connection(ConnectionInfo(data_model_name=self.data_model_name, model_id=item_id))
    

    def generate_graphql_endpoint(self):
        """
        Generates a GraphQL endpoint for the given data model and adds it to the middleware.
        """
        for top_level_model_type in self.data_model.get_top_level_types():
            self.create_query_for_model(top_level_model_type)
            # TODO: also make mutation possible
            # self.create_mutation_for_model(top_level_model_type)
        schema = graphene.Schema(query=self.query)
        graphql_app = GraphQLApp(schema=schema, on_get=make_graphiql_handler())
        self.middleware.app.mount("/graphql", graphql_app)


    def resolve_optional_and_union_types(self, models: typing.List[typing.Tuple[str, typing.Type[Submodel]]]):
        resolved_models = []
        for _, model in models:
            if not typing.get_origin(model) is typing.Union:
                resolved_models.append(model)
                continue
            submodels = typing.get_args(model)
            for submodel in submodels:
                if not submodel is NoneType:
                    resolved_models.append(submodel)

        return resolved_models
    
    def create_query_for_model(self, model_type: type):
        model_name = model_type.__name__

        submodels = get_contained_models_attribute_info(model_type)
        submodel_type_list = self.resolve_optional_and_union_types(submodels)
        graphene_submodels = []
        for submodel in submodel_type_list:
            graphene_submodels.append(
                create_graphe_pydantic_output_type_for_submodel_elements(submodel)
            )

        for submodel, graphene_submodel in zip(submodel_type_list, graphene_submodels):
            submodel_name = submodel.__name__
            class_dict = {
                f"{submodel_name}": graphene.List(graphene_submodel),
                f"resolve_{submodel_name}": self.get_submodel_resolve_function(submodel),
            }
            self.query = type("Query", (self.query,), class_dict)


        graphene_model = create_graphe_pydantic_output_type_for_model(model_type)

        class_dict = {
            f"{model_name}": graphene.List(graphene_model),
            f"resolve_{model_name}": self.get_aas_resolve_function(model_type),
        }
        self.query = type("Query", (self.query,), class_dict)

    def get_aas_resolve_function(self, model: typing.Type[BaseModel]) -> typing.Callable:
        """
        Returns the resolve function for the given pydantic model.

        Args:
            model (Type[BaseModel]): Pydantic model for which the resolve function should be created.

        Returns:
            typing.Callable: Resolve function for the given pydantic model.
        """
        middleware_instance = self.middleware
        async def resolve_models(self, info):
            aas_list = []
            connection_infos = middleware_instance.persistence_registry.get_type_connection_info(model.__name__)
            for connection_info in connection_infos:
                connector = middleware_instance.persistence_registry.get_connection(connection_info)
                retrieved_aas: AAS = await connector.provide()
                aas = model.model_validate(retrieved_aas.model_dump())
                aas_list.append(aas)
            return aas_list

        resolve_models.__name__ = f"resolve_{model.__name__}"
        return resolve_models


    def get_submodel_resolve_function(self, model: typing.Type[BaseModel]) -> typing.Callable:
        """
        Returns the resolve function for the given pydantic model.

        Args:
            model (Type[BaseModel]): Pydantic model for which the resolve function should be created.

        Returns:
            typing.Callable: Resolve function for the given pydantic model.
        """
        middleware_instance = self.middleware

        async def resolve_models(self, info):
            submodel_list = []
            connection_infos = middleware_instance.persistence_registry.get_type_connection_info(model.__name__)
            for connection_info in connection_infos:
                connector = middleware_instance.persistence_registry.get_connection(connection_info)
                retrieved_submodel: Submodel = await connector.provide()
                submodel = model.model_validate(retrieved_submodel.model_dump())
                submodel_list.append(submodel)
            return submodel_list

        resolve_models.__name__ = f"resolve_{model.__name__}"
        return resolve_models


def add_class_method(model: typing.Type):
    def is_type_of(cls, root, info):
        return isinstance(root, (cls, model))

    class_method = classmethod(is_type_of)
    model.is_type_of = class_method


model_name_registry = set()


def create_graphe_pydantic_output_type_for_model(
    input_model: typing.Type[BaseModel], union_type: bool = False
) -> PydanticObjectType:
    """
    Creates a pydantic model for the given pydantic model.

    Args:
        model (Type[BaseModel]): Pydantic model for which the Graphene Object Type should be created.

    Returns:
        PydanticObjectType: Graphene Object type for the given pydantic model.
    """
    graphene_model_registry = get_global_registry(PydanticObjectType)._registry
    for model in graphene_model_registry.keys():
        if input_model == model.__name__:
            return graphene_model_registry[model]

    rework_default_list_to_default_factory(input_model)
    graphene_model = type(
        input_model.__name__,
        (PydanticObjectType,),
        {"Meta": type("Meta", (), {"model": input_model})},
    )
    if union_type:
        add_class_method(graphene_model)

    return graphene_model


def is_typing_list_or_tuple(input_type: typing.Any) -> bool:
    """
    Checks if the given type is a typing.List or typing.Tuple.

    Args:
        input_type (typing.Any): Type to check.

    Returns:
        bool: True if the given type is a typing.List or typing.Tuple, False otherwise.
    """
    return typing.get_origin(input_type) == list or typing.get_origin(input_type) == tuple


def is_optional_typing_list_or_tuple(input_type: typing.Any) -> bool:
    """
    Checks if the given type is an optional typing.List or typing.Tuple.

    Args:
        input_type (typing.Any): Type to check.

    Returns:
        bool: True if the given type is an optional typing.List or typing.Tuple, False otherwise.
    """
    if not typing.get_origin(input_type) is typing.Union:
        return False
    non_optional_type = [t for t in typing.get_args(input_type) if t is not NoneType]
    return is_typing_list_or_tuple(non_optional_type[0])


def list_contains_any_submodel_element_collections(
    input_type: typing.Union[typing.List, typing.Tuple]
) -> bool:
    try:
        return any(
            issubclass(nested_type, SubmodelElementCollection)
            for nested_type in typing.get_args(input_type)
        )
    except TypeError:
        return False


def rework_default_list_to_default_factory(model: BaseModel):
    for names, field in model.model_fields.items():
        if field.default:
            pass
        if (
            isinstance(field.default, list)
            or isinstance(field.default, tuple)
            or isinstance(field.default, set)
        ):
            if field.default:
                field.annotation = type(field.default[0])
            else:
                # TODO: potentially remove this...
                field.annotation = typing.List[str]
            field.default = None
        if isinstance(field.default, BaseModel):
            field.default = None


def create_graphe_pydantic_output_type_for_submodel_elements(
    model: Submodel, union_type: bool = False
) -> PydanticObjectType:
    """
    Create recursively graphene pydantic output types for submodels and submodel elements.

    Args:
        model (typing.Union[base.Submodel, base.SubmodelElementCollectiontuple, list, set, ]): Submodel element for which the graphene pydantic output types should be created.
    """
    for attribute_value in get_all_submodel_elements_from_submodel(
        model
    ).values():
        if is_basemodel_union_type(attribute_value) or is_optional_basemodel_type(attribute_value):
            subtypes = typing.get_args(attribute_value)
            for subtype in subtypes:
                if subtype is NoneType:
                    continue
                create_graphe_pydantic_output_type_for_submodel_elements(
                    subtype, union_type=True
                )
        elif hasattr(attribute_value, "model_fields") and issubclass(
            attribute_value, SubmodelElementCollection
        ):
            create_graphe_pydantic_output_type_for_submodel_elements(attribute_value)
        elif hasattr(attribute_value, "model_fields") and issubclass(
            attribute_value, Blob
        ):
            create_graphe_pydantic_output_type_for_model(Blob, union_type)
        elif hasattr(attribute_value, "model_fields") and issubclass(
            attribute_value, File
        ):
            create_graphe_pydantic_output_type_for_model(File, union_type)
        # FIXME: handle optional list here....
        elif is_typing_list_or_tuple(attribute_value) or is_optional_typing_list_or_tuple(attribute_value):
            if is_optional_typing_list_or_tuple(attribute_value):
                attribute_value = [t for t in typing.get_args(attribute_value) if t is not NoneType][0]
            if not list_contains_any_submodel_element_collections(attribute_value):
                continue
            for nested_type in typing.get_args(attribute_value):
                if is_basemodel_union_type(nested_type) or is_optional_basemodel_type(nested_type):
                    subtypes = typing.get_args(nested_type)
                    for subtype in subtypes:
                        if subtype is NoneType:
                            continue
                        create_graphe_pydantic_output_type_for_submodel_elements(
                            subtype, union_type=True
                        )
                elif issubclass(nested_type, SubmodelElementCollection):
                    create_graphe_pydantic_output_type_for_submodel_elements(
                        nested_type
                    )
    return create_graphe_pydantic_output_type_for_model(model, union_type)
