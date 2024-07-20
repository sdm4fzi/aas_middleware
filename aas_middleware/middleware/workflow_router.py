import asyncio
import functools
from inspect import signature
from types import NoneType
from typing import Dict, List
import typing

import anyio
from fastapi import APIRouter, BackgroundTasks, Body, HTTPException
from pydantic import BaseModel, Field, create_model
from aas_middleware.connect.workflows.worfklow_description import WorkflowDescription
from aas_middleware.connect.workflows.workflow import Workflow


def get_partial_type_hints(partial_func):
    original_func = partial_func.func
    original_hints = typing.get_type_hints(original_func)
    
    sig = signature(original_func)
    params = sig.parameters
    
    fixed_args = partial_func.args
    fixed_keywords = partial_func.keywords
    
    for index, param in enumerate(params.keys()):
        if index < len(fixed_args):
            original_hints.pop(param, None)
    
    for key in fixed_keywords.keys():
        original_hints.pop(key, None)
    
    return original_hints


def get_base_model_from_type_hints(name: str, type_hints: Dict[str, typing.Any]) -> typing.Type[BaseModel]:
    """
    Get the base model from the type hints of a function.

    Args:
        type_hints (Dict[str, typing.Any]): Type hints of a function.

    Returns:
        typing.Type[typing.Any]: Base model of the type hints.
    """
    if "return" in type_hints:
        type_hints.pop("return")
    dynamical_model_creation_dict = {}
    for argument, argument_type in type_hints.items():
        entry = {
            argument: typing.Annotated[
                argument_type, Field()
            ]
        }
        dynamical_model_creation_dict.update(entry)
    base_model = create_model(f"body_for_{name}", **dynamical_model_creation_dict)
    return base_model


def generate_workflow_endpoint(workflow: Workflow) -> List[APIRouter]:
    """
    Generates endpoints for a workflow to execute the workflow.

    Args:
        workflow (Workflow): Workflow that contains the function to be executed by the workflow.

    Returns:
        APIRouter: FastAPI router with an endpoint to execute the workflow.
    """
    router = APIRouter(
        prefix=f"/workflows/{workflow.get_name()}",
        tags=["workflows"],
        responses={404: {"description": "Not found"}},
    )

    if isinstance(workflow.workflow_function, functools.partial):
        type_hints = get_partial_type_hints(workflow.workflow_function)
    else:
        type_hints = typing.get_type_hints(workflow.workflow_function)
    
    return_type = type_hints.pop("return") if "return" in type_hints else None
    if len(type_hints) == 0:
        input_type_hints = None
    elif len(type_hints) == 1:
        input_type_hints = list(type_hints.values())[0]
    else:
        input_type_hints = get_base_model_from_type_hints(workflow.get_name(), type_hints)


    if input_type_hints is None:
        if workflow.get_description().interval is None:
            @router.post("/execute", response_model=return_type)
            async def execute():
                if workflow.running:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Workflow {workflow.get_name()} is already running. Wait for it to finish or interrupt it first.",
                    )
                return await workflow.execute()

        @router.post("/execute_background", response_model=Dict[str, str])
        async def execute_background(background_tasks: BackgroundTasks):
            if workflow.running:
                raise HTTPException(
                    status_code=400,
                    detail=f"Workflow {workflow.get_name()} is already running. Wait for it to finish or interrupt it first.",
                )
            background_tasks.add_task(workflow.execute)
            return {"message": f"Started exeuction of workflow {workflow.get_name()}"}
    else:
        if workflow.get_description().interval is None:
            @router.post("/execute", response_model=return_type)
            # TODO: make the optional not here, but add a method that updates the POST endpoints after a connection is added, to have optional parameters...
            async def execute(arg: typing.Optional[input_type_hints]=None): # type: ignore
                if workflow.running:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Workflow {workflow.get_name()} is already running. Wait for it to finish or interrupt it first.",
                    )
                if isinstance(arg, BaseModel) and len(type_hints) > 1:
                    input_value = dict(arg)
                    return await workflow.execute(**input_value)
                else:
                    return await workflow.execute(arg)

        @router.post("/execute_background", response_model=Dict[str, str])
        async def execute_background(background_tasks: BackgroundTasks, arg: typing.Optional[input_type_hints]=None): # type: ignore
            if workflow.running:
                raise HTTPException(
                    status_code=400,
                    detail=f"Workflow {workflow.get_name()} is already running. Wait for it to finish or interrupt it first.",
                )
            if isinstance(arg, BaseModel) and len(type_hints) > 1:
                input_value = dict(arg)
                background_tasks.add_task(workflow.execute, **input_value)
            else:
                background_tasks.add_task(workflow.execute, arg.model_dump())
            return {"message": f"Started exeuction of workflow {workflow.get_name()}"}
        

    @router.get("/description", response_model=WorkflowDescription)
    async def describe_workflow():
        return workflow.get_description()

    @router.get("/interrupt", response_model=Dict[str, str])
    async def interrupt_workflow():
        try:
            await workflow.interrupt()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"message": f"Stopped execution of workflow {workflow.get_name()}"}

    return router
