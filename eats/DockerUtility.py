import logging
import os
import time
import typing

import docker

from eats.constant import PROJECT_ROOT


class DockerContainerConfig:
    """
    Configuration class for Docker container setup.

    Attributes:
        imageid (str): ID of the Docker image.
        volumes (dict): Volumes to be mounted in the container.
        environment (list): List of environment variables for the container.
        command (str): Command to run in the container.
        detach (bool): Whether to run the container in detached mode.
    """

    imageid: str
    volumes: typing.Dict[str, typing.Dict[str, str]]
    environment: typing.List[str]
    command: str
    detach: bool
    working_dir: str

    def __init__(self, imageid, volumes, environment, command, detach=True):
        self.imageid = imageid
        self.volumes = volumes
        self.environment = environment
        self.command = command
        self.detach = detach


class ContainerTimeoutError(Exception):
    pass


def build_docker_image(target_program_root: str, tag: str, log_path: typing.Optional[str]=None, nocache=False) \
        -> typing.Tuple[docker.models.images.Image, str]:
    """
    Build a Docker image from a Dockerfile.

    Args:
        target_program_root (str): Path to the target program root.
        tag (str, optional): Tag for the Docker image. Defaults to 'eats:latest'.
        log_path (str, optional): Path to the log file. Defaults to None.

    Returns:
        Tuple[docker.models.images.Image, str]: Built image and logs.
    """
    image, logs = docker.from_env().images.build(
        path=PROJECT_ROOT,
        tag=tag,
        dockerfile=os.path.join(PROJECT_ROOT, 'eats', 'docker_scripts', 'Dockerfile'),
        rm=True,
        buildargs={'TARGET_PROGRAM_ROOT': os.path.relpath(target_program_root, PROJECT_ROOT)},
        nocache=nocache
    )
    if log_path:
        with open(log_path, "w") as f:
            for line in logs:
                f.write(str(line) + "\n")
    return image, logs


def wait_for_container(container: docker.models.containers.Container, timeout: int, log_file_path: typing.Optional[str]=None) -> typing.Tuple[int, str]:
    """
    Wait for a Docker container to finish execution or timeout.

    Args:
        container (docker.models.containers.Container): Docker container instance.
        timeout (int): Maximum wait time in seconds.
        log_file (str, optional): Path to the log file. Defaults to None.

    Returns:
        Tuple[int, str]: Exit code and logs of the container.
    """
    if log_file_path:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    start_time = time.time()
    try:
        while True:
            container.reload()
            if container.status != 'running':
                break
            if time.time() - start_time > timeout:
                raise ContainerTimeoutError(f"Container {container.id[:10]} timed out after {timeout} seconds")
            if log_file_path:
                logs = container.logs()
                with open(log_file_path, "w") as f:
                    f.write(logs.decode())
            time.sleep(5)
    except ContainerTimeoutError:
        container.stop()
        logging.warning(f"Container {container.id[:10]}, stopped due to timeout")
    except KeyboardInterrupt:
        container.stop()
        logging.warning(f"Container {container.id[:10]}, stopped due to KeyboardInterrupt")
        raise
    except Exception as e:
        container.stop()
        logging.warning(f"Container {container.id[:10]}, stopped due to {e}")
        raise e

    exit_code = container.wait()['StatusCode']
    logs = container.logs()
    if log_file_path:
        with open(log_file_path, "w") as f:
            f.write(logs.decode())
    container.remove()
    return exit_code, logs, time.time() - start_time


def create_docker_container(docer_config: DockerContainerConfig) -> docker.models.containers.Container:
    """
    Create and run a Docker container based on the provided configuration.

    Args:
        docker_config (DockerContainerConfig): Configuration object for the Docker container.

    Returns:
        docker.models.containers.Container: Docker container instance.
    """

    for k in docer_config.volumes:
        assert k.startswith('/'), f"Volume {k} must be absolute path. Got {k}"
        
    common_params = {
        'volumes': docer_config.volumes,
        'environment': docer_config.environment,
        'command': docer_config.command,
        'detach': docer_config.detach,
    }
    container = docker.from_env().containers.run(docer_config.imageid, **common_params)
    return container
