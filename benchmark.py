import json
import os
import eats.main
from eats.utility import module_find
from eats.Config import Config

from lxml import etree

def collect_report_data(path, report_folder):
    data = {}
    path_to_coverage = os.path.join(path, report_folder, "cov_report", "coverage.json")
    data["coverage"] = json.load(open(path_to_coverage))["totals"]["percent_covered"]

    path_to_mutmut = os.path.join(path, report_folder, "mutmut_report.json")
    data["mutation_score"] = json.load(open(path_to_mutmut))["arithmetic_mean_killed"]

    return data

def collect_benchmark_data_flutils():
    config = Config()
    TARGET_PROGRAM_ROOT = "./targets/flutils"
    config.TARGET_PROGRAM_ROOT = TARGET_PROGRAM_ROOT
    config.MAX_WORKERS = 10
    config.working_dir = "benchmark_flutils2"
    modules_to_test = ["flutils/**/*.py"]
    ignore_modules = ["**/__*.py"]
    max_modules_to_test = 300
    config.max_pynguin_search_time_first_search = 1200 # 300 + 300 + 600
    config.max_pynguin_iterations_first_search = 1000000
    config.imprve_with_fuzzing = False
    config.max_pynguin_search_time_second_search = 300
    config.max_pynguin_iterations_second_search = 1000000
    config.max_mutmut_time = 1200
    config.max_fuzz_time = 600
    config.max_fuzz_iterations = 100000000

    modules_to_test = [os.path.join(TARGET_PROGRAM_ROOT, x) for x in modules_to_test if x.strip()]
    ignore_modules = [os.path.join(TARGET_PROGRAM_ROOT, x) for x in ignore_modules if x.strip()]
    modules = module_find(TARGET_PROGRAM_ROOT, modules_to_test, ignore_modules)[:max_modules_to_test]
    if len(modules) == 0:
        print("No modules to test")
        return
    config.module_names = modules

    if not config.working_dir.startswith("/"):
        config.working_dir = os.path.abspath(config.working_dir)

    eats.main.main(config=config)

    config.max_pynguin_search_time_first_search = 300
    config.max_pynguin_iterations_first_search = 1000000
    config.imprve_with_fuzzing = True
    config.working_dir = "benchmark_flutils_fuzzing2"
    if not config.working_dir.startswith("/"):
        config.working_dir = os.path.abspath(config.working_dir)
    eats.main.main(config=config)

    result = {"project": "flutils", "hash": "***"}
    result["pynguin"] = collect_report_data("benchmark_flutils2", "report1")
    result["pynguin+atheris"] = collect_report_data("benchmark_flutils_fuzzing2", "report2")

    return result

def collect_benchmark_data_httpie():
    config = Config()
    TARGET_PROGRAM_ROOT = "./targets/cli"
    config.TARGET_PROGRAM_ROOT = TARGET_PROGRAM_ROOT
    config.MAX_WORKERS = 10
    config.working_dir = "benchmark_httpie"
    modules_to_test = ["httpie/**/*.py"]
    ignore_modules = ["**/__*.py"]
    max_modules_to_test = 300
    config.max_pynguin_search_time_first_search = 1200 # 300 + 300 + 600
    config.max_pynguin_iterations_first_search = 1000000
    config.imprve_with_fuzzing = False
    config.max_pynguin_search_time_second_search = 300
    config.max_pynguin_iterations_second_search = 1000000
    config.max_mutmut_time = 1200
    config.max_fuzz_time = 600
    config.max_fuzz_iterations = 100000000

    modules_to_test = [os.path.join(TARGET_PROGRAM_ROOT, x) for x in modules_to_test if x.strip()]
    ignore_modules = [os.path.join(TARGET_PROGRAM_ROOT, x) for x in ignore_modules if x.strip()]
    modules = module_find(TARGET_PROGRAM_ROOT, modules_to_test, ignore_modules)[:max_modules_to_test]
    if len(modules) == 0:
        print("No modules to test")
        return
    config.module_names = modules

    if not config.working_dir.startswith("/"):
        config.working_dir = os.path.abspath(config.working_dir)

    eats.main.main(config=config)

    config.max_pynguin_search_time_first_search = 300
    config.max_pynguin_iterations_first_search = 1000000
    config.imprve_with_fuzzing = True
    config.working_dir = "benchmark_httpie_fuzzing"
    if not config.working_dir.startswith("/"):
        config.working_dir = os.path.abspath(config.working_dir)
    eats.main.main(config=config)

    result = {"project": "httpie", "hash": "***"}
    result["pynguin"] = collect_report_data("benchmark_httpie", "report1")
    result["pynguin+atheris"] = collect_report_data("benchmark_httpie_fuzzing", "report2")

    return result

if __name__ == "__main__":
    # print(collect_benchmark_data_flutils())
    print(collect_benchmark_data_httpie())
