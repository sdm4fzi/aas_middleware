import typing
import aas_middleware
import time


middleware = aas_middleware.Middleware()


@middleware.workflow()
def long_running_workflow(a: str) -> str:
    print("long_running_workflow")
    time.sleep(5)
    return a


@middleware.workflow(blocking=True)
def long_running_workflow_blocking(a: str) -> str:
    print("long_running_workflow_blocking")
    time.sleep(5)
    return a


@middleware.workflow(blocking=True, pool_size=3)
def long_running_workflow_blocking3(a: str) -> str:
    print("long_running_workflow_blocking3")
    time.sleep(5)
    return a

@middleware.workflow(queueing=True)
def long_running_workflow_queuing(a: str) -> str:
    print("long_running_workflow_queuing")
    time.sleep(5)
    return a

@middleware.workflow(queueing=True, pool_size=3)
def long_running_workflow_queuing3(a: str) -> str:
    print("long_running_workflow_queuing3")
    time.sleep(5)
    return a


if __name__ == "__main__":
    import uvicorn


    # uvicorn.run("test_workflow:middleware.app", reload=True)
    uvicorn.run(middleware.app)
