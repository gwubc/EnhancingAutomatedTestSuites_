import glob
import os
import typing


def _module_find_all(PROJECT_ROOT: str, path_to_modules: str) -> typing.List[str]:
    """
    Find all Python modules in the specified path.

    Args:
        PROJECT_ROOT (str): The root directory of the project.
        path_to_modules (str): The glob pattern to find the modules.

    Returns:
        List[str]: A sorted list of module names.
    """
    modules = []
    for file in glob.glob(path_to_modules, recursive = True):
        if not file.endswith(".py"):
            continue
        subpath = os.path.relpath(file, PROJECT_ROOT)
        moduleName = subpath.replace("/", ".")[:-3]
        if moduleName not in modules:
            modules.append(moduleName)
    modules = sorted(modules)
    return modules


def module_find(PROJECT_ROOT: str, path_to_modules: typing.List[str], ignores: typing.List[str]=None) -> typing.List[str]:
    """
    Find all Python modules in the specified paths, excluding the ignored paths.

    Args:
        PROJECT_ROOT (str): The root directory of the project.
        path_to_modules (List[str]): List of glob patterns to find the modules.
        ignores (List[str], optional): List of glob patterns to ignore. Defaults to None.

    Returns:
        List[str]: A list of module names that are not in the ignored paths.
    """
    modules = []
    ignores_ = []
    for path_to_module in path_to_modules:
        modules += _module_find_all(PROJECT_ROOT, path_to_module)
    if ignores:
        for ignore in ignores:
            ignores_ += _module_find_all(PROJECT_ROOT, ignore)
    return [module for module in modules if module not in ignores_]
