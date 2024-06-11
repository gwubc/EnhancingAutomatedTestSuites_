import eats.logging_config

import concurrent.futures
import logging
import os

from eats.Config import Config
from eats.DockerUtility import build_docker_image
from eats.Evaluate import create_reports
from eats.GenerateTestWithPynguin import create_test_with_pynguin
from eats.ImproveUseFuzzer import ImproveUseFuzzer


def main(config: Config) -> int:
    """
    Main function to build Docker image, run Pynguin tests, create coverage report,
    and evaluate with Mutmut.

    Args:
        config (Config): Configuration object.

    Returns:
        int: Exit code.
    """

    if not config.module_names:
        logging.error("No modules to test")
        return 1
    
    if not os.path.exists(config.working_dir):
        os.makedirs(config.working_dir)
    if not os.path.exists(os.path.join(config.working_dir, "logs")):
        os.makedirs(os.path.join(config.working_dir, "logs"))
    
    image, logs = build_docker_image(config.TARGET_PROGRAM_ROOT, 
                                     "eats:latest",
                                     f"{config.working_dir}/logs/build.log")

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        futures = [executor.submit(create_test_with_pynguin,
                                   module,
                                   config.working_dir,
                                   config.max_pynguin_search_time_first_search,
                                   config.max_pynguin_iterations_first_search)
                   for module in config.module_names]
        concurrent.futures.wait(futures)
        [future.result() for future in futures]  # Check for exceptions
        
        create_reports(config.working_dir, 
                       config.module_names, 
                       [f'{config.working_dir}/tests/pynguin_results'], 
                       "report1", 
                       config.max_mutmut_time + 300, 
                       config.MAX_WORKERS)
        if not config.imprve_with_fuzzing:
            return 0
        pendings = [ImproveUseFuzzer(module,
                                    config.working_dir, 
                                    config.max_fuzz_time,
                                    config.max_fuzz_iterations,
                                    config.max_pynguin_search_time_second_search,
                                    config.max_pynguin_iterations_second_search,
                                    config.max_mutmut_time) 
                    for module in config.module_names]
    
        futures = [executor.submit(p.run_transform) for p in pendings]
        concurrent.futures.wait(futures)
        [future.result() for future in futures]  # Check for exceptions

        fuzzs = []
        for p in pendings:
            fuzzs += p.create_fuzz_runner()
        futures = [executor.submit(f) for f in fuzzs]
        concurrent.futures.wait(futures)
        [future.result() for future in futures]  # Check for exceptions

        futures = [executor.submit(p.run_recreation_results) for p in pendings]
        concurrent.futures.wait(futures)
        [future.result() for future in futures]  # Check for exceptions
        futures = [executor.submit(p.run_pynguin) for p in pendings]
        concurrent.futures.wait(futures)
        [future.result() for future in futures]  # Check for exceptions
        create_reports(config.working_dir, 
                       config.module_names, 
                       [f'{config.working_dir}/tests/pynguin_results', f'{config.working_dir}/tests/finial_pynguin_results'], 
                       "report2", 
                       config.max_mutmut_time + 300, 
                       config.MAX_WORKERS)
        logging.info("Finished creating reports")
    return 0
