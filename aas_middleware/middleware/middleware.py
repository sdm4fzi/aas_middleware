from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from functools import partial
import typing
from pydantic import BaseModel, ConfigDict, Field
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from basyx.aas import model

import aas_middleware
from aas_middleware.connect.connectors.connector import Connector
from aas_middleware.connect.connectors.model_connector import ModelConnector
from aas_middleware.middleware import persistence_factory
from aas_middleware.middleware.connector_router import generate_connector_endpoint, generate_persistence_connector_endpoint
from aas_middleware.middleware.graphql_routers import GraphQLRouter
from aas_middleware.middleware.registries import ConnectionInfo, ConnectionRegistry, PersistenceConnectionRegistry, WorkflowRegistry
from aas_middleware.middleware.model_registry_api import generate_model_api
from aas_middleware.middleware.persistence_factory import PersistenceFactory
from aas_middleware.middleware.rest_routers import RestRouter
from aas_middleware.middleware.synchronization import synchronize_connector_with_persistence
from aas_middleware.middleware.workflow_router import generate_workflow_endpoint
from aas_middleware.connect.workflows.workflow import Workflow
from aas_middleware.model.core import Identifiable
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.formatting.aas.aas_middleware_util import get_pydantic_model_from_dict
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxFormatter
from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel



def get_license_info() -> str:
    return {
        "name": "MIT License",
        "url": "https://mit-license.org/",
    }

class MiddlewareMetaData(BaseModel):
    """
    Meta data for the middleware.
    """
    title: str = "aas-middleware"
    description: str = """
    The aas-middleware allows to convert aas models to pydantic models and generate a REST or GraphQL API from them.
    """
    version: str = Field(default=aas_middleware.VERSION)
    contact: typing.Dict[str, str] = {
        "name": "Sebastian Behrendt",
        "email": "sebastian.behrendt@kit.edu",
    }
    license_info: typing.Dict[str, str] = Field(init=False, default_factory=get_license_info)

    

class Middleware:
    """
    Middleware that can be used to generate a REST or GraphQL API from aas' and submodels either in pydanctic models or in aas object store format.
    """

    def __init__(self):
        self._app: typing.Optional[FastAPI] = None
        self.meta_data: MiddlewareMetaData = MiddlewareMetaData()

        self.data_models: typing.Dict[str, DataModel] = {}

        self.on_start_up_callbacks: typing.List[typing.Callable] = []
        self.on_shutdown_callbacks: typing.List[typing.Callable] = []

        self.persistence_registry: PersistenceConnectionRegistry = PersistenceConnectionRegistry()
        self.connection_registry: ConnectionRegistry = ConnectionRegistry()
        self.workflow_registry: WorkflowRegistry = WorkflowRegistry()

    def set_meta_data(self, title: str, description: str, version: str, contact: typing.Dict[str, str]):
        """
        Function to set the meta data of the middleware.

        Args:
            title (str): The title of the middleware.
            description (str): The description of the middleware.
            version (str): The version of the middleware.
            contact (typing.Dict[str, str]): The contact information of the middleware.
            license_info (typing.Dict[str, str]): The license information of the middleware.
        """
        self.meta_data = MiddlewareMetaData(
            title=title,
            description=description,
            version=version,
            contact=contact
        )

    def add_callback(self, callback_type: typing.Literal["on_start_up", "on_shutdown"], callback: typing.Callable, *args, **kwargs):
        """
        Function to add a callback to the middleware.

        Args:
            callback_type (typing.Literal["on_start_up", "on_shutdown"]): The type of the callback.
            callback (typing.Callable): The callback function.
        """
        functional_callback = partial(callback, *args, **kwargs)
        if callback_type == "on_start_up":
            self.on_start_up_callbacks.append(functional_callback)
        elif callback_type == "on_shutdown":
            self.on_shutdown_callbacks.append(functional_callback)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """
        Function to create a lifespan for the middleware for all events on startup and shutdown.

        Args:
            app (FastAPI): The FastAPI app that should be used for the lifespan.
        """
        for workflow in self.workflow_registry.get_workflows():
            if workflow.on_startup:
                # TODO: make a case distinction for workflows that postpone start up or not...
                asyncio.create_task(workflow.execute())
        for callback in self.on_start_up_callbacks:
            await callback()
        for connector in self.connection_registry.connectors.values():
            await connector.connect()
        for persistence in self.persistence_registry.connectors.values():
            await persistence.connect()
        yield
        for workflow in self.workflow_registry.get_workflows():
            if workflow.on_shutdown:
                if workflow.running:
                    await workflow.interrupt()
                await workflow.execute()

        for callback in self.on_shutdown_callbacks:
            await callback()

        for connector in self.connection_registry.connectors.values():
            await connector.disconnect()
        for persistence in self.persistence_registry.connectors.values():
            await persistence.disconnect()

    @property
    def app(self):
        if not self._app:
            app = FastAPI(
                title=self.meta_data.title,
                description=self.meta_data.description,
                version=self.meta_data.version,
                contact=self.meta_data.contact,
                license_info={
                    "name": "MIT License",
                    "url": "https://mit-license.org/",
                },
                lifespan=self.lifespan
            )

            app.add_middleware(
                # TODO: make CORS more sophisticated for individual connectors
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )
            self._app = app

            @app.get("/", response_model=str)
            async def root():
                return "Welcome to aas-middleware!"

        return self._app
    
    def load_data_model(self, name: str, data_model: DataModel, persist_instances: bool = False):
        """
        Function to load a data model into the middleware to be used for synchronization.

        Args:
            name (str): The name of the data model.
            data_model (DataModel): Data model containing the types and values.
            persist_instances (bool): If the instances of the data model should be persisted.
        """
        self.data_models[name] = data_model

        if persist_instances:
            for models_of_type in data_model.get_top_level_models().values():
                if not models_of_type:
                    continue
                model = models_of_type[0]

                for model in models_of_type:
                    self.add_callback("on_start_up", self.persist, name, model)

    def load_json_models(
        self,
        json_models: typing.Dict[str, typing.Any] = None,
        all_fields_required: bool = False,
    ):
        """
        Functions that loads models from a json dict into the middleware that can be used for synchronization.

        The function can either be used with a dict that contains the objects.

        Args:
            json_models (dict): Dictionary of aas' and submodels.
            all_fields_required (bool): If all fields are required in the models.
        """
        # TODO: use here the function to load a DataModel from a dict
        # for model_name, model_values in json_models.items():
        #     pydantic_model = get_pydantic_model_from_dict(
        #         model_values, model_name, all_fields_required
        #     )
        #     self.models.append(pydantic_model)

    def load_model_instances(self, name: str, instances: typing.List[BaseModel]):
        """
        Functions that loads pydantic models into the middleware as a datamodel that can be used for synchronization.

        Args:
            name (str): The name of the data model.
            instances (typing.List[BaseModel]): List of pydantic model instances.
        """
        data_model = DataModel.from_models(*instances)
        self.load_data_model(name, data_model)


    def load_pydantic_models(self, name: str, *models: typing.Tuple[typing.Type[BaseModel]]):
        """
        Functions that loads pydantic models into the middleware that can be used for synchronization.

        Args:
            models (typing.List[typing.Type[BaseModel]]): List of pydantic models.
        """
        data_model = DataModel.from_model_types(models)
        self.load_data_model(data_model)

    def load_aas_objectstore(self, models: model.DictObjectStore):
        """
        Functions that loads multiple aas and their submodels into the middleware that can be used for synchronization.

        Args:
            models (typing.List[model.DictObjectStore]): Object store of aas' and submodels
        """
        data_model = BasyxFormatter().deserialize(models)
        self.load_data_model(data_model)

    async def update_value(self, value: typing.Any, data_model_name: str, model_id: typing.Optional[str]=None, contained_model_id: typing.Optional[str]=None, field_name: typing.Optional[str]=None):
        """
        Function to update a value in the persistence.

        Args:
            data_model_name (str): _description_
            model_id (typing.Optional[str]): _description_
            field_name (typing.Optional[str]): _description_
            value (typing.Any): _description_
        """
        connection_info = ConnectionInfo(data_model_name=data_model_name, model_id=model_id, contained_model_id=contained_model_id, field_id=field_name)
        try:
            connector = self.persistence_registry.get_connection(connection_info)
            await connector.consume(value)
        except KeyError as e:
            await self.persist(data_model_name, value)
        
    async def get_value(self, data_model_name: str, model_id: typing.Optional[str]=None, contained_model_id: typing.Optional[str]=None, field_name: typing.Optional[str]=None) -> typing.Any:
        """
        Function to get a value from the persistence.

        Args:
            data_model_name (str): _description_
            model_id (typing.Optional[str]): _description_
            field_name (typing.Optional[str]): _description_

        Returns:
            typing.Any: _description_
        """
        connection_info = ConnectionInfo(data_model_name=data_model_name, model_id=model_id, contained_model_id=contained_model_id, field_id=field_name)
        try:
            connector = self.persistence_registry.get_connection(connection_info)
            return await connector.provide()
        except KeyError:
            raise KeyError(f"No provider found for {connection_info}")
    
    def add_default_persistence(self, persistence_factory: PersistenceFactory, data_model_name: typing.Optional[str], model_id: typing.Optional[Identifiable], model_type: typing.Type[typing.Any] = typing.Any):
        """
        Function to add a default persistence for a model.

        Args:
            data_model_name (str): The name of the data model.
            model (Identifiable): The model that should be persisted.
        """
        if not data_model_name in self.data_models:
            raise ValueError(f"No data model {data_model_name} found.")
        
        connection_info = ConnectionInfo(data_model_name=data_model_name, model_id=model_id, contained_model_id=None, field_id=None)
        self.persistence_registry.add_persistence_factory(connection_info, model_type, persistence_factory)
    

    async def persist(self, data_model_name: str, model: typing.Optional[Identifiable]=None, persistence_factory: typing.Optional[PersistenceFactory]=None):
        """
        Function to add a model to the persistence.

        Args:
            data_model_name (str): The name of the data model.
            model (Identifiable): The model that should be persisted.
            persistence_factory (PersistenceFactory): The persistence factory that should be used.

        Raises:
            ValueError: If the connection already exists.
        """
        connection_info = ConnectionInfo(data_model_name=data_model_name, model_id=model.id, contained_model_id=None, field_id=None)
        if connection_info in self.persistence_registry.connections:
            raise ValueError(f"Connection {connection_info} already exists. Try using the existing connector or remove it first.")
        self.persistence_registry.add_to_persistence(connection_info, model, persistence_factory)
        connector = self.persistence_registry.get_connection(connection_info)
        # TODO: raise an error if consume is not possible and remove the persistence in the persistence registry
        await connector.consume(model)


    def add_connector(self, connector_id: str, connector: Connector, model_type: typing.Type[typing.Any], data_model_name: typing.Optional[str]=None, model_id: typing.Optional[str]=None, contained_model_id: typing.Optional[str]=None, field_id: typing.Optional[str]=None):
        """
        Function to add a connector to the middleware.

        Args:
            connector_id (str): The name of the connector.
            connector (Connector): The connector that should be added.
        """
        self.connection_registry.add_connector(connector_id, connector, model_type)
        if data_model_name:
            self.connect_connector_to_persistence(connector_id, data_model_name, model_id, contained_model_id, field_id)
            self.generate_rest_endpoint_for_connector(connector_id, ConnectionInfo(data_model_name=data_model_name, model_id=model_id, contained_model_id=contained_model_id, field_id=field_id))	
        else:
            self.generate_rest_endpoint_for_connector(connector_id)


    def generate_rest_endpoint_for_connector(self, connector_id: str, connection_info: typing.Optional[ConnectionInfo]=None):
        """
        Function to generate a REST endpoint for a connector.

        Args:
            connector_id (str): _description_
            connection_info (typing.Optional[ConnectionInfo], optional): _description_. Defaults to None.

        Raises:
            ValueError: _description_
        """
        if not connector_id in self.connection_registry.connectors:
            raise ValueError(f"Connector {connector_id} not found.")
        connector = self.connection_registry.get_connector(connector_id)
        model_type = self.connection_registry.connection_types[connector_id]
        if not connection_info:
            router = generate_connector_endpoint(connector_id, connector, model_type)
        else:
            router = generate_persistence_connector_endpoint(connector_id, connector, connection_info, model_type)
        self.app.include_router(router)


    # TODO: handle also async connectors!!
        

    def connect_connector_to_persistence(self, connector_id: str, data_model_name: str, model_id: typing.Optional[str]=None, contained_model_id: typing.Optional[str]=None, field_id: typing.Optional[str]=None):
        """
        Function to connect a connector to a data entity in the middleware.

        Args:
            connector_id (str): The name of the connector.
            connector (Connector): The connector that should be connected.
            data_model_name (str): The name of the data model used for identifying the data model in the middleware.
            model_id (typing.Optional[str], optional): The id of the model in the data model. Defaults to None.
            field_id (typing.Optional[str], optional): The id of the field in the model. Defaults to None.
            model_type (typing.Type[typing.Any], optional): The type of the model. Defaults to typing.Any.
        """
        connection_info = ConnectionInfo(data_model_name=data_model_name, model_id=model_id, contained_model_id=contained_model_id, field_id=field_id)
        connector = self.connection_registry.get_connector(connector_id)
        type_connection_info = self.connection_registry.connection_types[connector_id]
        self.connection_registry.add_connection(connector_id, connection_info, connector, type_connection_info)

        synchronize_connector_with_persistence(connector, connection_info, self.persistence_registry)

    def workflow(
        self,
        *args,
        on_startup: bool = False,
        on_shutdown: bool = False,
        interval: typing.Optional[float] = None,
        **kwargs
    ):
        def decorator(func):
            workflow = Workflow.define(
                func,
                *args,
                on_startup=on_startup,
                on_shutdown=on_shutdown,
                interval=interval,
                **kwargs
            )
            self.workflow_registry.add_workflow(workflow)
            workflows_app = generate_workflow_endpoint(workflow)
            self.app.include_router(workflows_app)
            return func

        return decorator

    def generate_model_registry_api(self):
        """
        Adds a REST API so that new models can be registered and unregistered from the Middleware.
        """
        # TODO: validate if this works and add it to the admin api...
        router = generate_model_api(middleware_instance=self)
        self.app.include_router(router)
        NUM_REGISTRY_ROUTES = len(router.routes)
        NUM_CONSTANT_ROUTES = 5
        self.app.router.routes = (
            self.app.router.routes[:NUM_CONSTANT_ROUTES]
            + self.app.routes[-NUM_REGISTRY_ROUTES:]
            + self.app.routes[NUM_CONSTANT_ROUTES:-NUM_REGISTRY_ROUTES]
        )

    def generate_rest_api_for_data_model(self, data_model_name: str):
        """
        Generates a REST API with CRUD operations for aas' and submodels from the loaded models.
        """
        data_model = self.data_models[data_model_name]
        rest_router = RestRouter(data_model, data_model_name, self)
        rest_router.generate_endpoints()
        
    def generate_graphql_api_for_data_model(self, data_model_name: str):
        """
        Generates a GraphQL API with query operations for aas' and submodels from the loaded models.
        """
        data_model = self.data_models[data_model_name]
        graphql_router = GraphQLRouter(data_model, data_model_name, self)
        graphql_router.generate_graphql_endpoint()



