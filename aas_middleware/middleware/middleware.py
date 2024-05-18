import asyncio
import typing
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from basyx.aas import model

import aas_middleware
from aas_middleware.connect.consumers.consumers import Consumer
from aas_middleware.connect.providers.provider import Provider
from aas_middleware.middleware.model_registry_api import generate_model_api
from aas_middleware.middleware.rest_routers import RestRouter
from aas_middleware.middleware.workflow_router import generate_workflow_endpoint
from aas_middleware.connect.workflows.workflow import Workflow
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.formatting.aas.aas_formatter import AASFormatter
from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel


class Middleware:
    """
    Middleware that can be used to generate a REST or GraphQL API from aas' and submodels either in pydanctic models or in aas object store format.
    """

    def __init__(self):
        # TODO: adjust that the types in the middleware are DataModels.
        self.data_models: typing.Dict[str, DataModel] = {}
        
        self._app: typing.Optional[FastAPI] = None
        

        # TODO: add methods that automatically instantiate these dicts here
        self._persistence_providers: typing.Dict[str, typing.Dict[str, Provider[AAS, Submodel]]]
        self._persistence_consumers: typing.Dict[str, typing.Dict[str, Consumer[AAS, Submodel]]]


        self._workflows: typing.List[Workflow] = []

    async def start_up(self):
        """
        Function starts the mainloop of the middleware running all continuous workflows and
        doing all polling http requestors.
        """
        for workflow in self._workflows:
            if workflow.on_startup:
                # TODO: make a case distinction for workflows that postpone start up or not...
                asyncio.create_task(workflow.execute())

    async def shutdown(self):
        """
        Function stops all continuous workflows and polling http requestors.
        """
        for workflow in self._workflows:
            if workflow.on_shutdown:
                if workflow.running:
                    await workflow.interrupt()
                await workflow.execute()

    @property
    def app(self):
        if not self._app:
            # TODO: update the meta data
            description = """
             The aas-middleware allows to convert aas models to pydantic models and generate a REST or GraphQL API from them.
                """

            app = FastAPI(
                title="aas-middelware",
                description=description,
                version=aas_middleware.VERSION,
                contact={
                    "name": "Sebastian Behrendt",
                    "email": "sebastian.behrendt@kit.edu",
                },
                license_info={
                    "name": "MIT License",
                    "url": "https://mit-license.org/",
                },
                on_startup=[self.start_up],
                on_shutdown=[self.shutdown],
            )

            app.add_middleware(
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
    
    def load_data_model(self, name: str, data_model: DataModel):
        """
        Function to load a data model into the middleware to be used for synchronization.

        Args:
            name (str): The name of the data model.
            data_model (DataModel): Data model containing the types and values.
        """
        self.data_models[name] = data_model

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
        """
        if not json_models:
            raise ValueError("Either json_models or file_path must be specified.")
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

    def load_pydantic_models(self, name: str, models: typing.List[typing.Type[BaseModel]]):
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
        data_model = AASFormatter().deserialize(models)
        self.load_data_model(data_model)

    def get_persistence_provider(self, data_model_name: str, model_id: typing.Optional[str]=None) -> Provider[AAS | Submodel]:
        """
        Function returns a persistence provider based on the information mentioned.

        Args:
            data_model_name (str): The name of the data model used for identifying the data model in the middleware.
            model_name (typing.Optional[str], optional): The id of the model in the data model.

        Returns:
            Provider[AAS | Submodel]: The provider of the model.
        """
        return self._persistence_providers[data_model_name][model_id]
    
    def get_persistence_consumer(self, data_model_name: str, model_id: typing.Optional[str]=None) -> Consumer[AAS | Submodel]:
        """
        Function returns a persistence consumer based on the information mentioned.

        Args:
            data_model_name (str): The name of the data model used for identifying the data model in the middleware.
            model_name (typing.Optional[str], optional): The id of the model in the data model.

        Returns:
            Consumer[AAS | Submodel]: The provider of the model.
        """
        return self._persistence_consumers[data_model_name][model_id]



    def generate_model_registry_api(self):
        """
        Adds a REST API so that new models can be registered and unregistered from the Middleware.
        """
        router = generate_model_api(middleware_instance=self)
        self.app.include_router(router)
        NUM_REGISTRY_ROUTES = len(router.routes)
        NUM_CONSTANT_ROUTES = 5
        self.app.router.routes = (
            self.app.router.routes[:NUM_CONSTANT_ROUTES]
            + self.app.routes[-NUM_REGISTRY_ROUTES:]
            + self.app.routes[NUM_CONSTANT_ROUTES:-NUM_REGISTRY_ROUTES]
        )

    def generate_rest_api(self):
        """
        Generates a REST API with CRUD operations for aas' and submodels from the loaded models.
        """
        for data_model_name, data_model in self.data_models.items():
            rest_router = RestRouter(data_model, data_model_name, self)
            routers = rest_router.generate_endpoints()
            for router in routers:
                self.app.include_router(router)

    # def generate_graphql_api(self):
    #     """
    #     Generates a GraphQL API with query operations for aas' and submodels from the loaded models.
    #     """
    #     graphql_app = generate_graphql_endpoint(self.models)
    #     self.app.mount("/graphql", graphql_app)

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
            self._workflows.append(workflow)
            workflows_app = generate_workflow_endpoint(workflow)
            self.app.include_router(workflows_app)
            return func

        return decorator
