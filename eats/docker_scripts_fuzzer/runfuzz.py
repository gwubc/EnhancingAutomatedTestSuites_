import importlib
import json
import os
import shutil
import subprocess
import sys
import time

import psutil


def early_stop_process(process, timeout):
    while time.time() < timeout:
        if process.poll() is not None:
            return process.returncode
        p = psutil.Process(process.pid)
        cpu_usage = p.cpu_percent(interval=1)
        # print(f"CPU usage of the {process.args}: {cpu_usage}%")
        if cpu_usage < 3:
            process.terminate()
            return
        time.sleep(10)
    process.terminate()


def run_fuzz_test(test_path, out_path, atheris_runs, delete_tmp=True):
    max_run_time = 300
    if os.getenv('atheris_max_run_time'):
        max_run_time = int(os.getenv('atheris_max_run_time'))
    os.makedirs(out_path, exist_ok=True)
    process = subprocess.Popen(['python', test_path, f'-atheris_runs={atheris_runs}', out_path])
    early_stop_process(process, time.time() + max_run_time)
    module_name = test_path.replace('/', '.').replace('.py', '')
    if module_name.startswith('.'):
        module_name = module_name[1:]
    module = importlib.import_module(module_name)
    inputs = []
    for file in os.listdir(out_path):
        with open(os.path.join(out_path, file), 'br') as f:
            data = f.read()
        d = module.fuzz_reader(data)
        inputs.append(d)
    if delete_tmp:
        shutil.rmtree(out_path, ignore_errors=True)
    return inputs


def run(test_name, out_path):
    try:
        try:
            atheris_runs = os.getenv('atheris_runs')
            atheris_runs = int(atheris_runs)
        except Exception:
            atheris_runs = 100000
        print(f"Running {test_name}, atheris_runs={atheris_runs}")
        inputs = run_fuzz_test(os.path.join("/workplace/tests_transformed", test_name), os.path.join(out_path, f"tmp/{test_name}"), atheris_runs, delete_tmp=False)
        json.dump(inputs, open(os.path.join(out_path, f'{test_name}.json'), 'w'), indent=4)
        print(f"Finished {test_name}")
    except Exception as e:
        print(f"Error in {test_name}: {e}")
        return 1


if __name__ == '__main__':
    sys.path.append("/")
    run(os.environ['test_name'], '/workplace/fuzzed_results')

