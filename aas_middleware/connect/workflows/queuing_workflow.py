from typing import Any, Awaitable, Callable, List, Dict, Optional, Union

import anyio
import anyio.to_thread


from aas_middleware.connect.workflows.workflow import Workflow, typechecked_partial

class QueueingWorkflow(Workflow):
    """
    The queueing workflow class is a subclass of the Workflow class and is used to define workflows that are executed concurrently. The number of concurrently running workflows is limited to the pool size number. If another workflow is executed, it is queued until a slot is available.

    Args:
        workflow_function (Union[Awaitable[None], Callable[..., None]]): The workflow function to be executed.
        interval (Optional[float]): The interval in seconds in which the workflow function is executed.
        on_startup (bool, optional): If True, the workflow function is executed on startup. Defaults to False.
        on_shutdown (bool, optional): If True, the workflow function is executed on shutdown. Defaults to False.
        pool_size (int, optional): The number of concurrently running workflows. Defaults to 1.
    """
    def __init__(
        self,
        workflow_function: Union[Awaitable[None], Callable[..., None]],
        interval: Optional[float],
        on_startup: bool = False,
        on_shutdown: bool = False,
        pool_size: int = 1,
    ):
        super().__init__(workflow_function, interval, on_startup, on_shutdown)
        self.pool_size = pool_size
        self.semaphore = anyio.Semaphore(pool_size)

    @classmethod
    def define(
        cls,
        func: Awaitable,
        *args: List[Any],
        on_startup: bool,
        on_shutdown: bool,
        interval: Optional[float],
        pool_size: int=1,
        **kwargs: Dict[str, Any],
    ):
        workflow_function = typechecked_partial(func, *args, **kwargs)
        return cls(
            workflow_function=workflow_function,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            interval=interval,
            pool_size=pool_size,
        )

    async def _run_workflow_function(self, *args, **kwargs) -> Awaitable[Any]:
        async with self.semaphore:
            return await super()._run_workflow_function(*args, **kwargs)
