from pydantic import BaseModel


from typing import List, Optional


class WorkflowDescription(BaseModel):
    """
    Gives meta information about a workflow.

    Args:
        name (str): Name of the workflow.
        running (bool): If the workflow is currently running.
        on_startup (bool): If the workflow is executed on startup of the middleware.
        on_shutdown (bool): If the workflow is executed on shutdown of the middleware.
        interval (Optional[float]): Interval in seconds the workflow is executed.
        providers (List[str]): List of providers the workflow consumes data from.
        consumers (List[str]): List of consumers the workflow provides data to.
    """

    name: str
    running: bool
    on_startup: bool
    on_shutdown: bool
    interval: Optional[float]
    providers: List[str]
    consumers: List[str]
