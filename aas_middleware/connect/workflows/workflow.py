import inspect
from typing import Any, Awaitable, Callable, List, Dict, Optional, Union
import functools
import uuid

import anyio
from anyio.abc import TaskGroup
import anyio.to_thread
from exceptiongroup import ExceptionGroup, catch
import typeguard

from aas_middleware.connect.workflows.worfklow_description import WorkflowDescription

def typechecked_partial(func, *args, **kwargs):
    wrapped = typeguard.typechecked(func)
    return functools.partial(wrapped, *args, **kwargs)

class Workflow:
    """
    The Workflow class is used to define workflows that are executed. It allows to define a workflow function that is executed once or repeatedly. Also, execution of the workflow can be interrupted.

    Args:
        workflow_function (Union[Awaitable[None], Callable[..., None]]): The workflow function to be executed
        interval (Optional[float]): The interval in seconds in which the workflow function is executed
        on_startup (bool, optional): If True, the workflow function is executed on startup. Defaults to False.
        on_shutdown (bool, optional): If True, the workflow function is executed on shutdown. Defaults to False.
    """
    def __init__(
        self,
        workflow_function: Union[Awaitable[None], Callable[..., None]],
        interval: Optional[float],
        on_startup: bool = False,
        on_shutdown: bool = False,
    ):
        if not isinstance(workflow_function, functools.partial):
            workflow_function = typeguard.typechecked(workflow_function)
        self.workflow_function = workflow_function
        self.on_startup = on_startup
        self.on_shutdown = on_shutdown
        self.interval = interval
        self.task_groups: Dict[str, TaskGroup] = {}

    @property
    def running(self) -> bool:
        return len(self.task_groups) > 0

    def get_name(self) -> str:
        if self.workflow_function is None:
            raise ValueError(
                "No workflow function defined. Use the 'define' method to define a workflow function."
            )
        return self.workflow_function.func.__qualname__.split(".")[-1]

    def get_description(self) -> WorkflowDescription:
        return WorkflowDescription(
            name=self.get_name(),
            running=self.running,
            on_startup=self.on_startup,
            on_shutdown=self.on_shutdown,
            interval=self.interval,
            consumers=[],
            providers=[],
        )

    @classmethod
    def define(
        cls,
        func: Awaitable,
        *args: List[Any],
        on_startup: bool,
        on_shutdown: bool,
        interval: Optional[float],
        **kwargs: Dict[str, Any],
    ):
        workflow_function = typechecked_partial(
            func, *args, **kwargs
        )
        return cls(
            workflow_function=workflow_function,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            interval=interval
        )

    async def _run_workflow_function(self, *args, **kwargs) -> Awaitable[Any]:
        if inspect.iscoroutinefunction(self.workflow_function):
            return await self.workflow_function(*args, **kwargs)
        else:
            partial_func = functools.partial(
                self.workflow_function, *args, **kwargs
            )
            return await anyio.to_thread.run_sync(
                partial_func, abandon_on_cancel=True
            )

    def handle_error(self, excgroup: ExceptionGroup, execution_id: str) -> None:
        for exc in excgroup.exceptions:
            if execution_id in self.task_groups:
                del self.task_groups[execution_id]
            raise RuntimeError(f"Error during execution of workflow: {str(exc)}".replace("\"", "'"))

    async def execute(self, *args, **kwargs) -> Awaitable[Any]:
        """
        Args:
            *args: list of arguments
            **kwargs: dictionary of keyword arguments

        Raises:
            RuntimeError: Error during execution of workflow

        Returns:
            Awaitable[Any]: return value of the workflow function
        """
        if not self.interval or self.interval == 0.0:
            return_value = await self._execute_once(*args, **kwargs)
            return return_value
        else:
            await self._execute_repeatedly(*args, **kwargs)

    async def _execute_once(self, *args, **kwargs) -> Awaitable[None]:
        execution_id = str(uuid.uuid4())
        handle_error_partial = functools.partial(self.handle_error, execution_id=execution_id)
        with catch({Exception: handle_error_partial}):
            async with anyio.create_task_group() as tg:
                self.task_groups[execution_id] = tg
                return_value = await self._run_workflow_function(*args, **kwargs)
                del self.task_groups[execution_id]
                return return_value
            if execution_id in self.task_groups:
                del self.task_groups[execution_id]
                raise RuntimeError("Workflow was interrupted.")

    async def _execute_repeatedly(self, *args, **kwargs) -> Awaitable[None]:
        execution_id = str(uuid.uuid4())
        handle_error_partial = functools.partial(self.handle_error, execution_id=execution_id)
        with catch({Exception: handle_error_partial}):
            async with anyio.create_task_group() as tg:
                self.task_groups[execution_id] = tg
                while True:
                    await self._run_workflow_function(*args, **kwargs)
                    await anyio.sleep(self.interval)
            del self.task_groups[execution_id]

    async def interrupt(self):
        if not self.running:
            raise ValueError("No workflow is running.")
        for _, task_group in self.task_groups.items():
            if task_group.cancel_scope.cancel_called or task_group.cancel_scope.cancelled_caught:
                continue
            task_group.cancel_scope.cancel()
