"""
Example usage of the refactored middleware system.

This example demonstrates the fluent builder interface and
automatic persistence connector creation.
"""

import asyncio
from facade.builder import AppBuilder
from utils.logging import setup_logging


async def main():
    """Main example function."""
    # Setup logging
    setup_logging(level="INFO")
    
    print("Building middleware application...")
    
    # Build the application using the fluent interface
    app = (
        AppBuilder()
            .meta(title="RheoNet MW", version="1.0.0")
            .models("shop", types=["Order", "Job"])
            .persistence(kind="memory")
            .connector("erp", kind="http_in", path="/erp/orders")
            .connector("scheduler", kind="http_out", url="http://sched:8080/plan")
            .bind("connector:erp", "persist:shop/Order", direction="push")
            .bind("persist:shop/Order.plan", "connector:scheduler", direction="push")
            .chain("plan_order")
                .receive("connector:erp")
                .map("erp_to_order")
                .format("json", mode="serialize")
                .consume("connector:scheduler")
                .consume("persist:shop/Order.plan")
                .register()
            .discover(kind="consul", url="http://consul:8500")
            .expose("rest", path="/shop")
            .expose("admin")
            .serve(host="0.0.0.0", port=8000)
            .build()
    )
    
    print("Application built successfully!")
    print(f"Configuration: {app.config.dict()}")
    
    # Start the application
    print("Starting application...")
    await app.start()
    
    # Get status
    status = app.get_status()
    print(f"Application status: {status}")
    
    # Run a chain
    print("Running chain...")
    result = await app.run_chain("plan_order", {"test": "data"})
    print(f"Chain result: {result}")
    
    # Stop the application
    print("Stopping application...")
    await app.stop()
    
    print("Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
