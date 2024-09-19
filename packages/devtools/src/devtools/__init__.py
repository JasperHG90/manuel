import socket
import time
from contextlib import contextmanager
from typing import List, Optional

import coolname
import docker
import tenacity


@tenacity.retry(
    stop=tenacity.stop_after_attempt(5),
    wait=tenacity.wait_exponential_jitter(initial=1),
)
def _wait_for_container(host: str = "localhost", port: int = 8080):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((host, port))
    except socket.error as e:
        raise ConnectionError("Container is not ready yet") from e
    finally:
        sock.close()


def _stop_existing_containers(
    image_name_prefix: str,
):
    """It's an unfortunate side-effect of VSCode debugger that it doesn't seem
    to stop the containers properly."""
    client = docker.from_env()
    for container in client.containers.list(
        all=True, filters={"name": f"{image_name_prefix}-*"}
    ):
        container.stop()


@contextmanager
def run_container(
    image: str,
    image_name_prefix: str,
    command: Optional[List[str]] = None,
    port_container_readiness_check: Optional[int] = None,
    wait_seconds: Optional[int] = None,
    **container_kwargs,
):
    """Context manager managing docker container lifecycle."""
    client = docker.from_env()
    client.images.pull(image, platform=container_kwargs.get("platform", None))
    _stop_existing_containers(image_name_prefix)
    try:
        container = client.containers.run(
            image=image,
            command=command,
            detach=True,
            remove=True,
            auto_remove=True,
            name=f"{image_name_prefix}-{coolname.generate_slug(2)}",
            **container_kwargs,
        )
        if port_container_readiness_check:
            _wait_for_container(port=port_container_readiness_check)
        if wait_seconds:
            time.sleep(wait_seconds)
        yield container
        container.stop()
    finally:
        ...
