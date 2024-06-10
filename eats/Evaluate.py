import logging
import typing
import concurrent.futures

from eats.DockerUtility import (DockerContainerConfig, create_docker_container,
                                wait_for_container)


def create_cov_report(working_dir: str, timeout: int, out_folder: str, paths_to_tests: typing.List[str]) -> int:
    """
    Create a coverage report by running a Docker container.

    Args:
        working_dir (str): Working directory path.
        timeout (int, optional): Timeout in seconds.
        out_folder (str): Output folder name.
        paths_to_tests (typing.List[str]): List of paths to the tests.

    Returns:
        int: Exit code of the container.
    """
    volumes={
            f'{working_dir}/{out_folder}/cov_report': {'bind': '/workplace/cov_report', 'mode': 'rw'},
            f'{working_dir}/{out_folder}/share_data': {'bind': '/workplace/share_data', 'mode': 'rw'},
        }
    for i, path in enumerate(paths_to_tests):
        volumes[path] = {'bind': f'/workplace/tests/{i}', 'mode': 'ro'}

    container = create_docker_container(DockerContainerConfig(
        imageid="eats:latest",
        volumes=volumes,
        environment=[],
        command='bash /usr/src/scripts/create_cov_report.sh',
        detach=True,
    ))
    logging.info("Running create_cov_report, container.id: %s", container.id[:10])
    exit_code, log, time_used = wait_for_container(container, timeout, f"{working_dir}/logs/{out_folder}/cov_report/cov_report.log")
    logging.info("create_cov_report exited with %d", exit_code)
    return exit_code, log, time_used


def evaluate_with_mutmut(module: str, working_dir: str, timeout: int, out_folder: str, paths_to_tests: typing.List[str]) -> int:
    """
    Evaluate the module with mutmut by running a Docker container.

    Args:
        module (str): Name of the module to evaluate.
        working_dir (str): Working directory path.
        timeout (int, optional): Timeout in seconds. Defaults to 600 seconds.
        out_folder (str): Output folder name.
        paths_to_tests (typing.List[str]): List of paths to the tests.
        
    Returns:
        int: Exit code of the container.
    """

    volumes={
            f'{working_dir}/{out_folder}/share_data': {'bind': '/workplace/share_data', 'mode': 'ro'},
            f'{working_dir}/{out_folder}/mutmut_cache/{module}/mutmut_report': {'bind': '/workplace/mutmut_report', 'mode': 'rw'},
        }
    for i, path in enumerate(paths_to_tests):
        volumes[path] = {'bind': f'/workplace/tests/{i}', 'mode': 'ro'}

    container = create_docker_container(DockerContainerConfig(
        imageid="eats:latest",
        volumes=volumes,
        environment=[f'module_name={module}'],
        command='bash /usr/src/scripts/evaluate_with_mutmut.sh',
        detach=True,
    ))
    logging.info("Running mutmut: %s, container.id: %s", module, container.id[:10])
    exit_code, log, time_used = wait_for_container(container, timeout, f"{working_dir}/logs/{out_folder}/mutmut/{module}.log")
    logging.info("mutmut %s exited with %d, time_used: %.2f seconds", module, exit_code, time_used)
    return exit_code, log, time_used

def report_mutmut_results(working_dir: str, timeout: int, modules: typing.List[str], src_dir: str) -> dict:
    """
    Report the mutmut results.

    Args:
        working_dir (str): Working directory path.
        timeout (int, optional): Timeout in seconds. Defaults to 600 seconds.
        modules (typing.List[str]): List of modules.
        src_dir (str): Source directory name.

    Returns:
        dict: Exit code, logs, and time used.
    """

    container = create_docker_container(DockerContainerConfig(
        imageid="eats:latest",
        volumes={
            f'{working_dir}/{src_dir}/mutmut_cache': {'bind': '/workplace/mutmut_cache', 'mode': 'ro'},
            f'{working_dir}/{src_dir}': {'bind': '/workplace/mutmut_report', 'mode': 'rw'},
        },
        environment=[f'module_names={",".join(modules)}'],
        command='python /usr/src/scripts/report.py',
        detach=True,
    ))
    logging.info("Running report_mutmut_results, container.id: %s", container.id[:10])
    exit_code, log, time_used = wait_for_container(container, timeout, f"{working_dir}/logs/{src_dir}/report_mutmut_results.log")
    logging.info("report_mutmut_results exited with %d, time_used: %.2f seconds", exit_code, time_used)
    return exit_code, log, time_used

def create_reports(working_dir: str, modules: typing.List[str], paths_to_tests: typing.List[str], out_folder: str, timeout: int, max_workers: int=1) -> dict:
    """
    Create coverage report and evaluate with mutmut.
    
    Args:
        working_dir (str): Working directory path.
        modules (typing.List[str]): List of modules.
        paths_to_tests (typing.List[str]): List of paths to the tests.
        out_folder (str): Output folder name.
        timeout (int, optional): Timeout in seconds.
        max_workers (int, optional): Maximum number of workers. Defaults to 1.
        
    Returns:
        dict: Exit code, logs, and time used."""
    
    create_cov_report(working_dir, timeout, out_folder, paths_to_tests)
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(max_workers)) as executor:
        futures = [executor.submit(evaluate_with_mutmut,
                                   module, working_dir,
                                   timeout,
                                   out_folder,
                                   paths_to_tests)
                   for module in modules]
        concurrent.futures.wait(futures)
        results = [future.result() for future in futures]
    report_mutmut_results(working_dir, timeout, modules, out_folder)