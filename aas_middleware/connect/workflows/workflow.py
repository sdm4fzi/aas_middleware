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
        workflow_function = functools.partial(
            func, *args, **kwargs
        )
        return cls(
            workflow_function=workflow_function,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            interval=interval,
        )

    async def _run_workflow_function(self, *args, **kwargs) -> Awaitable[Any]:
        if self.workflow_function is None:
            raise ValueError(
                "No workflow function defined. Use the 'define' method to define a workflow function."
            )
        sig = inspect.signature(self.workflow_function)
        try:
            bound_args = sig.bind(*args, **kwargs)
        except TypeError as e:
            raise ValueError(
                f"Decorated arguments do not match function signature of workflow function: {e}"
            )       
        if inspect.iscoroutinefunction(self.workflow_function):
            return await self.workflow_function(*bound_args.args, **bound_args.kwargs)
        else:
            partial_func = functools.partial(self.workflow_function, *bound_args.args, **bound_args.kwargs)
            return await anyio.to_thread.run_sync(
                partial_func, abandon_on_cancel=True
            )

    async def execute(self, *args, **kwargs) -> Awaitable[Any]:
        if self._task_group is not None:
            raise ValueError(
                "Workflow already started. Either wait for it to finish or interrupt it first."
            )
        if not self.interval or self.interval == 0.0:
            return await self._execute_once(*args, **kwargs)

        else:
            await self._execute_repeatedly(*args, **kwargs)

    async def _execute_once(self, *args, **kwargs) -> Awaitable[None]:
        async with anyio.create_task_group() as tg:
            self._task_group = tg
            return_value = await self._run_workflow_function(*args, **kwargs)
        self._task_group = None
        return return_value

    async def _execute_repeatedly(self, *args, **kwargs) -> Awaitable[None]:
        async with anyio.create_task_group() as tg:
            self._task_group = tg
            while True:
                await self._run_workflow_function(*args, **kwargs)
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
