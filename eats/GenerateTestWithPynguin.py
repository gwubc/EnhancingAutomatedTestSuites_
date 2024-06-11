import logging

from eats.DockerUtility import (DockerContainerConfig, create_docker_container,
                                wait_for_container)


def create_test_with_pynguin(module: str, working_dir: str, maximum_search_time: int, maximum_iterations: int) -> int:
    """
    Create test cases for a module using Pynguin by running a Docker container.

    Args:
        module (str): Name of the module to test.
        working_dir (str): Working directory path.
        maximum_search_time (int, optional): Maximum search time in seconds for Pynguin.
        maximum_iterations (int, optional): Maximum number of iterations for Pynguin.

    Returns:
        int: Exit code of the container.
    """
    container = create_docker_container(DockerContainerConfig(
        imageid="eats:latest",
        volumes={f'{working_dir}/tests/pynguin_results/{module}': {'bind': '/workplace/pynguin-results', 'mode': 'rw'}},
        environment=[f'module_name={module}',
                     f'maximum_search_time={maximum_search_time}',
                     f'maximum_iterations={maximum_iterations}'],
        command='bash /usr/src/scripts/create_test_with_pynguin.sh',
        detach=True,
    ))
    logging.info("Running pynguin: %s, container.id: %s", module, container.id[:10])
    exit_code, log, time_used = wait_for_container(container, maximum_search_time + 300, f"{working_dir}/logs/pynguin/{module}.log")
    logging.info("pynguin %s exited with %s, time used: %.2f seconds", module, exit_code, time_used)
    return exit_code
