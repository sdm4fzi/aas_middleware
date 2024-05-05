from typing import Any, Awaitable, Callable, List, Dict, Optional, Union
import functools
import inspect

import anyio
from anyio.abc import TaskGroup
import anyio.to_thread

from aas_middleware.connect.workflows.worfklow_description import WorkflowDescription


class Workflow:
    def __init__(
        self,
        workflow_function: Union[Awaitable[None], Callable[..., None]],
        interval: Optional[float],
        on_startup: bool = False,
        on_shutdown: bool = False,
    ):
        self.workflow_function = workflow_function
        self.on_startup = on_startup
        self.on_shutdown = on_shutdown
        self.interval = interval

        self._task_group: Optional[TaskGroup] = None

    @property
    def running(self) -> bool:
        return self._task_group is not None

    def get_name(self) -> str:
        if self.workflow_function is None:
            raise ValueError(
                "No workflow function defined. Use the 'define' method to define a workflow function."
            )
        return self.workflow_function.func.__qualname__

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
        sig = inspect.signature(func)
        try:
            bound_args = sig.bind(*args, **kwargs)
        except TypeError as e:
            raise ValueError(
                f"Decorated arguments do not match function signature of function '{func.__qualname__}': {e}"
            )
        # TODO: make a check, that the args and kwargs are only consumers or providers
        # TODO: add an option, whether the workflow is run in the background of fastAPI or it is waited for
        workflow_function = functools.partial(
            func, *bound_args.args, **bound_args.kwargs
        )
        return cls(
            workflow_function=workflow_function,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            interval=interval,
        )

    async def _run_workflow_function(self) -> Awaitable[None]:
        if self.workflow_function is None:
            raise ValueError(
                "No workflow function defined. Use the 'define' method to define a workflow function."
            )
        if inspect.iscoroutinefunction(self.workflow_function):
            await self.workflow_function()
        else:
            await anyio.to_thread.run_sync(
                self.workflow_function, abandon_on_cancel=True
            )

    async def execute(self) -> Awaitable[None]:
        if self._task_group is not None:
            raise ValueError(
                "Workflow already started. Either wait for it to finish or interrupt it first."
            )
        if not self.interval or self.interval == 0.0:
            await self._execute_once()
        else:
            await self._execute_repeatedly()

    async def _execute_once(self) -> Awaitable[None]:
        async with anyio.create_task_group() as tg:
            self._task_group = tg
            await self._run_workflow_function()
        self._task_group = None

    async def _execute_repeatedly(self) -> Awaitable[None]:
        async with anyio.create_task_group() as tg:
            self._task_group = tg
            while True:
                await self._run_workflow_function()
                await anyio.sleep(self.interval)
        self._task_group = None

    async def interrupt(self):
        if self._task_group is None:
            raise ValueError("No workflow is running.")
        if (
            self._task_group.cancel_scope.cancel_called
            or self._task_group.cancel_scope.cancelled_caught
        ):
            raise ValueError("Workflow is already interrupted.")
        self._task_group.cancel_scope.cancel()
