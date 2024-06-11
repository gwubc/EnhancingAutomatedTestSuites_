import eats.logging_config

import datetime
import logging
import multiprocessing
import os

import psutil
import multiprocessing
import os
import eats.main
from eats.utility import module_find
from eats.Config import Config


if __name__ == "__main__":
    import configparser
    eats_config = configparser.ConfigParser()
    eats_config.read('eats.ini')
    config = Config()
    try:
        TARGET_PROGRAM_ROOT = eats_config['DEFAULT']['TARGET_PROGRAM_ROOT']
        config.TARGET_PROGRAM_ROOT = TARGET_PROGRAM_ROOT
        config.MAX_WORKERS = int(eats_config['DEFAULT']['MAX_WORKERS'])
        config.working_dir = eats_config['DEFAULT'].get('working_dir', '')
        modules_to_test = eats_config['DEFAULT'].get('modules_to_test', '').split(',')
        ignore_modules = eats_config['DEFAULT'].get('ignore_modules', '').split(',')
        max_modules_to_test = int(eats_config['DEFAULT']['max_modules_to_test'])
        config.max_pynguin_search_time_first_search = int(eats_config['DEFAULT']['max_pynguin_search_time_first_search'])
        config.max_pynguin_iterations_first_search = int(eats_config['DEFAULT']['max_pynguin_iterations_first_search'])
        config.max_pynguin_search_time_second_search = int(eats_config['DEFAULT']['max_pynguin_search_time_second_search'])
        config.max_pynguin_iterations_second_search = int(eats_config['DEFAULT']['max_pynguin_iterations_second_search'])
        config.max_mutmut_time = int(eats_config['DEFAULT']['max_mutmut_time'])
        config.max_fuzz_time = int(eats_config['DEFAULT']['max_fuzz_time'])
        config.max_fuzz_iterations = int(eats_config['DEFAULT']['max_fuzz_iterations'])
        config.imprve_with_fuzzing = eats_config['DEFAULT'].getboolean('imprve_with_fuzzing', True)
    except Exception as e:
        
        logging.error(f"Error in reading eats.ini: {e}")
        print("Error in reading eats.ini")
        exit(1)

    if config.MAX_WORKERS < 1:
        config.MAX_WORKERS = int((multiprocessing.cpu_count() - psutil.cpu_percent()) * 3/4)
        if config.MAX_WORKERS < 1:
            config.MAX_WORKERS = 1

    modules_to_test = [os.path.join(TARGET_PROGRAM_ROOT, x) for x in modules_to_test if x.strip()]
    ignore_modules = [os.path.join(TARGET_PROGRAM_ROOT, x) for x in ignore_modules if x.strip()]
    modules = module_find(TARGET_PROGRAM_ROOT, modules_to_test, ignore_modules)[:max_modules_to_test]
    config.module_names = modules

    if config.working_dir == "DEFAULT":
        working_dir = "./working_dir_"
        for i in range(1, 1000):
            if not os.path.exists(f"{working_dir}{i}"):
                working_dir = f"{working_dir}{i}"
                break
        config.working_dir = working_dir
    logging.info(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logging.info(f"PID: {os.getpid()}")
    logging.info(f"Target program root: {config.TARGET_PROGRAM_ROOT}")
    logging.info(f"Modules to test: {config.module_names}")
    logging.info(f"Save to: {config.working_dir}")
    logging.info(f"Max workers: {config.MAX_WORKERS}")


    if not config.working_dir.startswith("/"):
        config.working_dir = os.path.abspath(config.working_dir)

    eats.main.main(config=config)
