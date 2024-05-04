import asyncio
from typing import Dict, List

import anyio
from fastapi import APIRouter, BackgroundTasks, HTTPException
from aas_middleware.workflows.worfklow_description import WorkflowDescription
from aas_middleware.workflows.workflow import Workflow

def generate_workflow_endpoint(workflow: Workflow) -> List[APIRouter]:
    """
    Generates endpoints for a workflow to execute the workflow.

    Args:
        workflow (Workflow): Workflow that contains the function to be executed by the workflow.

    Returns:
        APIRouter: FastAPI router with an endpoint to execute the workflow.
    """
    router = APIRouter(
        prefix=f"/{workflow.get_name()}",
        tags=["workflows"],
        responses={404: {"description": "Not found"}},
    )

    @router.get("/execute", response_model=Dict[str, str])
    async def execute_workflow(background_tasks: BackgroundTasks):
        if workflow.running:
            raise HTTPException(status_code=400, detail=f"Workflow {workflow.get_name()} is already running. Wait for it to finish or interrupt it first.")
        background_tasks.add_task(workflow.execute)
        return {
            "message": f"Started exeuction of workflow {workflow.get_name()}"
        }
    
    @router.get("/description", response_model=WorkflowDescription)
    async def describe_workflow():
        return workflow.get_description()
    
    @router.get("/interrupt", response_model=Dict[str, str])
    async def interrupt_workflow():
        try:
            await workflow.interrupt()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {
            "message": f"Stopped execution of workflow {workflow.get_name()}"
        }
    
    return router
