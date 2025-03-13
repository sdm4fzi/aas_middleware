from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from functools import partial
import typing
from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from basyx.aas import model

import aas_middleware
from aas_middleware.connect.connectors.async_connector import AsyncConnector, Receiver
from aas_middleware.connect.connectors.connector import Connector
from aas_middleware.connect.workflows.blocking_workflow import BlockingWorkflow
from aas_middleware.connect.workflows.queuing_workflow import QueueingWorkflow
from aas_middleware.middleware.connector_router import generate_connector_endpoint, generate_synced_connector_endpoint
from aas_middleware.middleware.graphql_routers import GraphQLRouter
from aas_middleware.middleware.registries import ConnectionInfo, ConnectionRegistry, MapperRegistry, PersistenceConnectionRegistry, WorkflowRegistry
from aas_middleware.middleware.model_registry_api import generate_model_api
from aas_middleware.middleware.persistence_factory import PersistenceFactory
from aas_middleware.middleware.rest_routers import RestRouter
from aas_middleware.middleware.sync.synchronization import synchronize_workflow_with_persistence_consumer, synchronize_workflow_with_persistence_provider
from aas_middleware.middleware.workflow_router import generate_workflow_endpoint
from aas_middleware.connect.workflows.workflow import Workflow
from aas_middleware.model.core import Identifiable
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxFormatter
from aas_middleware.model.formatting.formatter import Formatter
from aas_middleware.model.mapping.mapper import Mapper
from aas_middleware.middleware.sync.synced_connector import SyncedConnector, SyncRole, SyncDirection, synchronize_connector_with_persistence


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

        self.mapper_registry: MapperRegistry = MapperRegistry()

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
        for connector in self.connection_registry.connectors.values():
            await connector.connect()
        for persistence in self.persistence_registry.connectors.values():
            await persistence.connect()
        for workflow in self.workflow_registry.get_workflows():
            if workflow.on_startup:
                asyncio.create_task(workflow.execute())
        for callback in self.on_start_up_callbacks:
            await callback()

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
        data_model = DataModel.from_model_types(*models)
        self.load_data_model(name, data_model)

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
        await self.persistence_registry.add_to_persistence(connection_info, model, persistence_factory)
        connector = self.persistence_registry.get_connection(connection_info)
        try:
            await connector.consume(model)
        except Exception as e:
            self.persistence_registry.remove_connection(connection_info)
            raise e

    def add_connector(self, connector_id: str, connector: Connector, model_type: typing.Type[typing.Any]):
        """
        Function to add a connector to the middleware.

        Args:
            connector_id (str): The name of the connector.
            connector (Connector): The connector that should be added.
            model_type (typing.Type[typing.Any]): The type of the connector.
        """
        self.connection_registry.add_connector(connector_id, connector, model_type)
        router = generate_connector_endpoint(connector_id, connector, model_type)
        self.app.include_router(router)

    def sync_connector(self, connector_id: str, data_model_name: str, model_id: typing.Optional[str]=None, contained_model_id: typing.Optional[str]=None, field_id: typing.Optional[str]=None, persistence_mapper: typing.Optional[Mapper]=None, external_mapper: typing.Optional[Mapper]=None, formatter: typing.Optional[Formatter]=None, sync_role: SyncRole=SyncRole.READ_WRITE, sync_direction: SyncDirection=SyncDirection.BIDIRECTIONAL):
        """
        Function to connect a connector to a data entity in the middleware.

        Args:
            connector_id (str): The name of the connector.
            data_model_name (str): The name of the data model used for identifying the data model in the middleware.
            model_id (typing.Optional[str], optional): The id of the model in the data model. Defaults to None.
            contained_model_id (typing.Optional[str], optional): The id of a contained model. Defaults to None.
            field_id (typing.Optional[str], optional): The id of the field in the model. Defaults to None.
            persistence_mapper (typing.Optional[Mapper], optional): The mapper that should be used. Defaults to None.
            external_mapper (typing.Optional[Mapper], optional): The mapper that should be used. Defaults to None.
            formatter (typing.Optional[Formatter], optional): The formatter that should be used. Defaults to None.
            sync_role (typing.Optional[SyncRole], optional): Role of the connector in synchronization. Defaults to SyncRole.READ_WRITE.
            sync_direction (typing.Optional[SyncDirection], optional): Direction of synchronization. Defaults to SyncDirection.BIDIRECTIONAL.
        """
        connection_info = ConnectionInfo(data_model_name=data_model_name, model_id=model_id, contained_model_id=contained_model_id, field_id=field_id)
        connector = self.connection_registry.get_connector(connector_id)
        type_connection_info = self.connection_registry.connection_types[connector_id]
        self.connection_registry.add_connection(connector_id, connection_info, connector, type_connection_info)
        async def initiate_sync():
            synced_connector = synchronize_connector_with_persistence(
                connector_id,
                connector,
                connection_info,
                self.persistence_registry,
                sync_role,
                sync_direction,
                persistence_mapper,
                external_mapper,
                formatter,
            )
            if isinstance(connector, Receiver):
                async def run_receive():
                    async for _ in synced_connector.receive():
                        pass
                asyncio.create_task(run_receive())
            # Replace the original connector with the synced one
            self.connection_registry.connectors[connector_id] = synced_connector
        self.add_callback("on_start_up", initiate_sync)

        router = generate_synced_connector_endpoint(
            connector_id, connector, connection_info, sync_role, sync_direction, type_connection_info
        )
        self.app.include_router(router)

    def workflow(
        self,
        *args,
        on_startup: bool = False,
        on_shutdown: bool = False,
        interval: typing.Optional[float] = None,
        blocking: bool = False,
        queueing: bool = False,
        pool_size: int = 1,
        **kwargs
    ):
        def decorator(func):
            if blocking and queueing:
                raise ValueError("Workflow cannot be both blocking and queuing.")
            if blocking:
                workflow = BlockingWorkflow.define(
                    func,
                    *args,
                    on_startup=on_startup,
                    on_shutdown=on_shutdown,
                    interval=interval,
                    pool_size=pool_size,
                    **kwargs
                )
            elif queueing:
                workflow = QueueingWorkflow.define(
                    func,
                    *args,
                    on_startup=on_startup,
                    on_shutdown=on_shutdown,
                    interval=interval,
                    pool_size=pool_size,
                    **kwargs
                )
            else:
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

    def connect_workflow_to_persistence_provider(self, workflow_id: str, arg_name: str, data_model_name: str, model_id: typing.Optional[str]=None, contained_model_id: typing.Optional[str]=None, field_id: typing.Optional[str]=None, persistence_mapper: typing.Optional[Mapper]=None, external_mapper: typing.Optional[Mapper]=None, formatter: typing.Optional[Formatter]=None):
        """
        Function to connect a workflow to a data entity in the middleware.

        Args:
            workflow_id (str): The name of the workflow.
            data_model_name (str): The name of the data model used for identifying the data model in the middleware.
            model_id (typing.Optional[str], optional): The id of the model in the data model. Defaults to None.
            field_id (typing.Optional[str], optional): The id of the field in the model. Defaults to None.
            mapper (typing.Optional[Mapper], optional): The mapper that should be used. Defaults to None.
            formatter (typing.Optional[Formatter], optional): The formatter that should be used. Defaults to None.
        """
        connection_info = ConnectionInfo(data_model_name=data_model_name, model_id=model_id, contained_model_id=contained_model_id, field_id=field_id)
        workflow = self.workflow_registry.get_workflow(workflow_id)
        synchronize_workflow_with_persistence_provider(workflow, arg_name, connection_info, self.persistence_registry, persistence_mapper, external_mapper, formatter)
        # TODO: update workflow endpoint to have optional arguments
        # TODO: register mappers, formatters in middleware and add endpoint for them, also add connection to workflow registry

    def connect_workflow_to_persistence_consumer(self, workflow_id: str, data_model_name: str, model_id: typing.Optional[str]=None, contained_model_id: typing.Optional[str]=None, field_id: typing.Optional[str]=None, external_mapper: typing.Optional[Mapper]=None, formatter: typing.Optional[Formatter]=None):
        """
        Function to connect a workflow to a data entity in the middleware.

        Args:
            workflow_id (str): The name of the workflow.
            data_model_name (str): The name of the data model used for identifying the data model in the middleware.
            model_id (typing.Optional[str], optional): The id of the model in the data model. Defaults to None.
            field_id (typing.Optional[str], optional): The id of the field in the model. Defaults to None.
            mapper (typing.Optional[Mapper], optional): The mapper that should be used. Defaults to None.
            formatter (typing.Optional[Formatter], optional): The formatter that should be used. Defaults to None.
        """
        connection_info = ConnectionInfo(data_model_name=data_model_name, model_id=model_id, contained_model_id=contained_model_id, field_id=field_id)
        workflow = self.workflow_registry.get_workflow(workflow_id)
        synchronize_workflow_with_persistence_consumer(workflow, connection_info, self.persistence_registry, external_mapper, formatter)
        # TODO: register mappers, formatters in middleware and add endpoint for them, also add connection to workflow registry

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
