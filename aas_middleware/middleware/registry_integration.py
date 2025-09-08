from __future__ import annotations

from abc import ABC, abstractmethod
import uuid
import aiohttp
import os
import socket
from urllib.parse import urlparse


from typing import TYPE_CHECKING

from aas_middleware import get_version

if TYPE_CHECKING:
    from aas_middleware.middleware.middleware import MiddlewareMetaData


def resolve_public_endpoint(default_host: str = "127.0.0.1", default_port: int = 8000):
    """
    Resolve the externally reachable host, port and base_url.

    Precedence:
    1) PUBLIC_BASE_URL           e.g. https://api.example.com:8443
    2) PUBLIC_HOST + PUBLIC_PORT
    3) PORT (port only) + best-effort host detection
    4) defaults (127.0.0.1:8000)

    Returns (host, port, scheme, base_url)
    """
    base = os.getenv("PUBLIC_BASE_URL")
    if base:
        p = urlparse(base)
        host = p.hostname or default_host
        port = p.port or (443 if p.scheme == "https" else 80)
        scheme = p.scheme or "http"
        base_url = f"{scheme}://{host}:{port}"
        # Normalize default ports
        if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
            base_url = f"{scheme}://{host}"
        return host, port, scheme, base_url

    host = os.getenv("PUBLIC_HOST")
    port = os.getenv("PUBLIC_PORT")

    if host and port:
        port = int(port)
        scheme = os.getenv("PUBLIC_SCHEME", "http")
        base_url = f"{scheme}://{host}:{port}"
        if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
            base_url = f"{scheme}://{host}"
        return host, port, scheme, base_url

    # Best-effort inference
    inferred_port = int(os.getenv("PORT", default_port))
    try:
        # This often resolves to the container's IP in the bridge network (not public)
        inferred_host = socket.gethostbyname(socket.gethostname())
        # Fallback if it resolves to a non-routable address
        if inferred_host.startswith("127.") or inferred_host == "0.0.0.0":
            inferred_host = default_host
    except Exception:
        inferred_host = default_host

    scheme = os.getenv("PUBLIC_SCHEME", "http")
    base_url = f"{scheme}://{inferred_host}:{inferred_port}"
    if (scheme == "https" and inferred_port == 443) or (
        scheme == "http" and inferred_port == 80
    ):
        base_url = f"{scheme}://{inferred_host}"
    return inferred_host, inferred_port, scheme, base_url


class RegistryIntegrator(ABC):
    def __init__(self, registry_url: str, middleware_meta_data: MiddlewareMetaData, host: str, port: int):
        self.registry_url = registry_url
        self.middleware_meta_data = middleware_meta_data
        self.host = host
        self.port = port

    @abstractmethod
    async def register(self):
        raise NotImplementedError("Subclasses must implement this method.")


class ConsulIntegrator(RegistryIntegrator):

    def __init__(self, 
                 registry_url: str,  host: str, port: int,
                 middleware_meta_data: MiddlewareMetaData):
        super().__init__(registry_url, middleware_meta_data, host, port)

    async def register(self):
        # service_host, service_port, scheme, base_url = resolve_public_endpoint(
        #     default_host=self.host,
        #     default_port=self.port,
        # )
        service_host = self.host
        service_port = self.port
        service_address = f"{service_host}:{service_port}"
        # Consul agent service definition with metadata reference
        # Store only essential info in Consul Meta, full metadata available via /metadata endpoint
        consul_payload = {
            "Name": self.middleware_meta_data.title,
            "ID": f"{self.middleware_meta_data.title}-{uuid.uuid4().hex}",
            "Address": service_address,
            "Tags": [f"aas-middleware:{get_version()}"],
            "Port": service_port,
            # Store minimal metadata in Consul Meta section
            "Meta": {
                "description": self.middleware_meta_data.description,
                "service_address": service_address,
                "api-docs": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json",  # Reference to full metadata endpoint
            },
            # Health check so the service shows as passing
            "Check": {
                "HTTP": f"http://{service_address}/health",
                "Interval": "10s",
                "Timeout": "2s",
                "DeregisterCriticalServiceAfter": "1m",
            },
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.put(
                f"{self.registry_url}/v1/agent/service/register",
                json=consul_payload,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Failed to register with Consul: {resp.status} {text}")
