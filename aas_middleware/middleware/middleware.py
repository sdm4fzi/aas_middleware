import asyncio
import typing
import anyio
from pydantic import BaseModel, parse_obj_as
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import json
from basyx.aas import model

import aas_middleware
# from aas_middleware.middleware.graphql_routers import generate_graphql_endpoint
# from aas_middleware.middleware.rest_routers import generate_endpoints_from_model
# from aas_middleware.middleware.model_registry_api import generate_model_api
# from aas_middleware.util.convert_util import set_example_values, get_pydantic_model_from_dict, get_pydantic_models_from_instances
from aas_middleware.middleware.workflow_router import generate_workflow_endpoint
from aas_middleware.connect.workflows.workflow import Workflow

class Middleware:
    """
    Middleware that can be used to generate a REST or GraphQL API from aas' and submodels either in pydanctic models or in aas object store format.
    """

    def __init__(self):
        self.models: typing.List[typing.Type[BaseModel]] = []
        self._app: typing.Optional[FastAPI] = None


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
            description = """
             The aas2openapi middleware allows to convert aas models to pydantic models and generate a REST or GraphQL API from them.
                """

            app = FastAPI(
                title="aas2openapi",
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
                on_shutdown=[self.shutdown]
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
                return "Welcome to aas2openapi Middleware!"

        return self._app

    def load_json_models(self, json_models: dict=None, file_path: str=None, all_fields_required: bool=False):
        """
        Functions that loads aas' and submodels from a json file into the middleware that can be used for synchronization.

        The function can either be used with a dict that contains the aas' and submodels or with a json file path, so the function reads the file.

        Args:
            json_models (dict): Dictionary of aas' and submodels.
            file_path (str): Path to the json file.
        """
        if not json_models and not file_path:
            raise ValueError("Either json_models or file_path must be specified.")
        if not json_models and file_path:
            with open(file_path) as json_file:
                json_models = json.load(json_file)
        for model_name, model_values in json_models.items():
            pydantic_model = get_pydantic_model_from_dict(model_values, model_name, all_fields_required)
            self.models.append(pydantic_model)

    def load_pydantic_model_instances(self, instances: typing.List[BaseModel]):
        """
        Functions that loads pydantic models into the middleware that can be used for synchronization.

        Args:
            instances (typing.List[BaseModel]): List of pydantic model instances.
        """
        self.models = get_pydantic_models_from_instances(instances)


    def load_pydantic_models(self, models: typing.List[typing.Type[BaseModel]]):
        """
        Functions that loads pydantic models into the middleware that can be used for synchronization.

        Args:
            models (typing.List[typing.Type[BaseModel]]): List of pydantic models.
        """
        self.models = models

    def load_aas_objectstore(self, models: model.DictObjectStore):
        """
        Functions that loads multiple aas and their submodels into the middleware that can be used for synchronization.

        Args:
            models (typing.List[model.DictObjectStore]): Object store of aas' and submodels
        """
        instances = aas2openapi.convert_object_store_to_pydantic_models(models)
        self.models = get_pydantic_models_from_instances(instances)


    def generate_model_registry_api(self):
        """
        Adds a REST API so that new models can be registered and unregistered from the Middleware. 
        """
        router = generate_model_api(middleware_instance=self)
        self.app.include_router(router)
        NUM_REGISTRY_ROUTES = len(router.routes)
        NUM_CONSTANT_ROUTES = 5
        self.app.router.routes = self.app.router.routes[:NUM_CONSTANT_ROUTES] + self.app.routes[-NUM_REGISTRY_ROUTES:] + self.app.routes[NUM_CONSTANT_ROUTES:-NUM_REGISTRY_ROUTES]

    def generate_rest_api(self):
        """
        Generates a REST API with CRUD operations for aas' and submodels from the loaded models.
        """
        for model in self.models:
            routers = generate_endpoints_from_model(model)
            for router in routers:
                self.app.include_router(router)

    # def generate_graphql_api(self):
    #     """
    #     Generates a GraphQL API with query operations for aas' and submodels from the loaded models.
    #     """
    #     graphql_app = generate_graphql_endpoint(self.models)
    #     self.app.mount("/graphql", graphql_app)


    def workflow(self, *args, on_startup: bool=False, on_shutdown: bool=False, interval: typing.Optional[float]=None, **kwargs):
        def decorator(func):
            workflow = Workflow.define(func, *args, on_startup=on_startup, on_shutdown=on_shutdown, interval=interval, **kwargs)
            self._workflows.append(workflow)
            workflows_app = generate_workflow_endpoint(workflow)
            self.app.include_router(workflows_app)
            return func
        return decorator


