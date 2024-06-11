import logging
import os

from eats.DockerUtility import (DockerContainerConfig, create_docker_container,
                                wait_for_container)


class ImproveUseFuzzer:
    """
    A class to run the fuzzer and pynguin to improve the use of a module.
    
    Attributes:
        module (str): The name of the module.
        working_dir (str): The working directory path.
        max_fuzz_time (int): The maximum time to run fuzz tests.
        max_fuzz_iterations (int): The maximum number of fuzz test iterations.
        maximum_pynguin_search_time (int): The maximum time to run Pynguin.
        maximum_pynguin_iterations (int): The maximum number of Pynguin iterations.
        timeout (int): The timeout for the container.
        health (bool): The health of the module.
        
    """

    def __init__(self, module: str, working_dir: str,
                     max_fuzz_time: int, max_fuzz_iterations: int,
                     maximum_pynguin_search_time: int, maximum_pynguin_iterations: int,
                     timeout: int) -> None:
        self.module = module
        self.working_dir = working_dir
        self.max_fuzz_time = max_fuzz_time
        self.max_fuzz_iterations = max_fuzz_iterations
        self.maximum_pynguin_search_time = maximum_pynguin_search_time
        self.maximum_pynguin_iterations = maximum_pynguin_iterations
        self.timeout = timeout
        self.health = True

    def run_transform(self):
        container = create_docker_container(DockerContainerConfig(
        imageid="eats:latest",
        volumes={f'{self.working_dir}/tests/pynguin_results/{self.module}': {'bind': '/workplace/tests', 'mode': 'ro'},
                 f'{self.working_dir}/intermediate_steps/transform/{self.module}': {'bind': '/workplace/tests_transformed', 'mode': 'rw'}},
        environment=['PYTHONPATH=/usr/src'],
        command='python /usr/src/scripts_fuzzer/transform.py',
        ))
        logging.info(f"Running transform: {self.module}, container.id: {container.id[:10]}")
        exit_code, log, time_used = wait_for_container(container, self.timeout, f"{self.working_dir}/logs/transform/{self.module}.log")
        logging.info(f"transform {self.module} exited with {exit_code}")
        if len(os.listdir(f'{self.working_dir}/intermediate_steps/transform/{self.module}')) == 0:
            logging.warning(f"No fuzz tests generated for {self.module}")
            self.health = False
        return exit_code, log, time_used
    
    def _fuzz_runner(self, fuzz_test):
        def fuzz_runner():
            container = create_docker_container(DockerContainerConfig(
            imageid="eats:latest",
            volumes={f'{self.working_dir}/intermediate_steps/transform/{self.module}': {'bind': '/workplace/tests_transformed', 'mode': 'ro'},
                    f'{self.working_dir}/intermediate_steps/fuzzed_results/{self.module}/{fuzz_test}': {'bind': '/workplace/fuzzed_results', 'mode': 'rw'}},
            environment=['PYTHONPATH=/usr/src', f'atheris_runs={self.max_fuzz_iterations}', f'atheris_max_run_time={self.max_fuzz_time}', f'test_name={fuzz_test}'],
            command='python /usr/src/scripts_fuzzer/runfuzz.py',
            ))
            logging.info(f"Running fuzzed_results: {self.module}::{fuzz_test}, container.id: {container.id[:10]}")
            exit_code, log, time_used = wait_for_container(container, self.max_fuzz_time  + 300, f"{self.working_dir}/logs/fuzzed_results/{self.module}/{fuzz_test}.log")
            logging.info(f"fuzzed_results {self.module}::{fuzz_test} exited with {exit_code}")
            return exit_code, log, time_used
        return fuzz_runner
        
    def create_fuzz_runner(self) -> list:
        if not self.health:
            return []
        fuzz_tests = [i for i in os.listdir(f'{self.working_dir}/intermediate_steps/transform/{self.module}') if i.endswith('.py')]
        if len(fuzz_tests) == 0:
            logging.warning(f"No fuzz tests found for {self.module}")
            self.health = False
            return []
        return [self._fuzz_runner(fuzz_test) for fuzz_test in fuzz_tests]
    
    def run_recreation_results(self):
        if not self.health:
            return 1, "No fuzz tests generated", 0
        container = create_docker_container(DockerContainerConfig(
            imageid="eats:latest",
            volumes={f'{self.working_dir}/tests/pynguin_results/{self.module}': {'bind': '/workplace/tests', 'mode': 'ro'},
                    f'{self.working_dir}/intermediate_steps/fuzzed_results/{self.module}': {'bind': '/workplace/tests_fuzzed_result', 'mode': 'ro'},
                    f'{self.working_dir}/intermediate_steps/recreation_results/{self.module}': {'bind': '/workplace/recreation_results', 'mode': 'rw'}},
            environment=[f'module_name={self.module}',  
                        'PYTHONPATH=/usr/src'],
            command='python /usr/src/scripts_fuzzer/RecreateTests.py',
        ))
        logging.info(f"Running recreation_results: {self.module}, container.id: {container.id[:10]}")
        exit_code, log, time_used = wait_for_container(container, self.timeout, f"{self.working_dir}/logs/recreation_results/{self.module}.log")
        logging.info(f"recreation_results {self.module} exited with {exit_code}")
        return exit_code, log, time_used
    
    def run_pynguin(self):
        if not self.health:
            return 1, "No fuzz tests generated", 0
        container = create_docker_container(DockerContainerConfig(
        imageid="eats:latest",
        volumes={f'{self.working_dir}/intermediate_steps/recreation_results/{self.module}': {'bind': '/workplace/recreation_results', 'mode': 'ro'},
                 f'{self.working_dir}/tests/finial_pynguin_results/{self.module}': {'bind': '/workplace/finial_pynguin_results', 'mode': 'rw'}},
        environment=[f'module_name={self.module}', 
                     f'maximum_search_time={self.maximum_pynguin_search_time}',
                     f'maximum_iterations={self.maximum_pynguin_iterations}', 
                     'PYTHONPATH=/usr/src/project'],
        command='bash /usr/src/scripts_fuzzer/run_pynguin.sh',
        ))
        logging.info(f"Running pynguin: {self.module}, container.id: {container.id[:10]}")
        exit_code, log, time_used = wait_for_container(container, self.maximum_pynguin_search_time + 300, f"{self.working_dir}/logs/finial_pynguin_results/{self.module}.log")
        logging.info(f"finial_pynguin_results {self.module} exited with {exit_code}")
        return exit_code, log, time_used
