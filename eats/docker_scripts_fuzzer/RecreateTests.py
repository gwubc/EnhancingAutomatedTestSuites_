import ast
import json
import os
import typing

import astor
import autoflake
import black


def has_decorator(func: ast.FunctionDef, decorator_name: str) -> bool:
    """
    Checks if a function has a specific decorator.

    Parameters:
    func (ast.FunctionDef): The function definition node from the abstract syntax tree (AST).
    decorator_name (str): The name of the decorator to check for.

    Returns:
    bool: True if the function has the specified decorator, False otherwise.
    """
    for decorator in func.decorator_list:
        if isinstance(decorator, ast.Call) and \
                isinstance(decorator.func, ast.Attribute):
            if decorator.func.attr == decorator_name:
                return True
    return False


def discover_tests(tree: ast.AST) -> typing.List[str]:
    """  # noqa: E501
    Discovers and returns a list of test function names from the given AST tree,
    excluding those with the 'xfail' decorator or that should be ignored based on custom checks.

    Parameters:
    tree (ast.AST): The abstract syntax tree (AST) representing the source code to analyze.

    Returns:
    list: A list of names of test functions that do not have the 'xfail' decorator and are not marked to be ignored.
    """
    function_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if has_decorator(node, "xfail"):
                continue
            check = TestCheck()
            check.visit(node)
            if check.should_ignore:
                continue
            function_names.append(node.name)
    return function_names


class TestCheck(ast.NodeTransformer):
    """  # noqa: E501
    A custom AST node transformer that checks for test functions with at least one constant that is in ['int', 'float', 'str', 'bool'].
    
    Attributes:
    should_ignore (bool): Indicates whether the function should be ignored based on the presence of constant assignments.
    """
    should_ignore = True

    def visit_FunctionDef(self, node):
        if node.name.startswith("test_"):
            [self.visit(stmt) for stmt in node.body]
        return node
    
    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name) and \
                (isinstance(node.value, ast.Constant)):
            type_name = type(node.value.value).__name__
            if type_name in ['int', 'float', 'str', 'bool']:
                self.should_ignore = False
        return node
    

class ImportCollector(ast.NodeVisitor):
    """
    Collects import statements from the AST.

    Attributes:
    imports (list): A list to store import statements found in the AST.
    """
    def __init__(self):
        self.imports = []
    
    def visit_Import(self, node):
        self.imports.append(node)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        self.imports.append(node)
        self.generic_visit(node)

    def get_imports(self):
        return ast.Module(body=self.imports, type_ignores=[])


class FunctionFinder(ast.NodeVisitor):
    """
    Finds functions with a specified name.

    Attributes:
    functions (list): A list to store function definition nodes with the target function name.
    target_function_name (str): The name of the target function to find.
    """
    def __init__(self, target_function_name: str):
        self.functions = []
        self.target_function_name = target_function_name
    
    def visit_FunctionDef(self, node):
        if node.name == self.target_function_name:
            self.functions.append(node)
        self.generic_visit(node)


class ValueChanger(ast.NodeTransformer):
    """
    Changes the values of specific variables in assignment statements.

    Attributes:
    new_values (dict): A dictionary mapping variable names to their new values.
    """
    def __init__(self, new_values: typing.Dict[str, typing.Any]):
        self.new_values = new_values

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name) and \
                (isinstance(node.value, ast.Constant)):
            new_value = self.new_values.get(node.targets[0].id, None)
            if new_value:
                node.value = ast.Constant(value=new_value)
        return node


class AssertRemover(ast.NodeTransformer):
    """
    Removes assert statements and raises.
    """
    def visit_Assert(self, node):
        return []
    
    def visit_With(self, node):
        for item in node.items:
            if (isinstance(item.context_expr, ast.Call) and
                    isinstance(item.context_expr.func, ast.Attribute) and
                    item.context_expr.func.attr == 'raises'):
                return node.body
        return self.generic_visit(node)
    

def RecreateTests(test_name: str, test_source: str, 
                  test_data: typing.List[typing.Dict], path_to_out: str):
    if len(test_data) == 0:
        return 1
    collector = ImportCollector()
    collector.visit(test_source)
    new_code = astor.to_source(collector.get_imports())

    finder = FunctionFinder(test_name)
    finder.visit(test_source)
    if len(finder.functions) == 0:
        return 1
    function = finder.functions[0]

    remover = AssertRemover()
    function = remover.visit(function)
    for data in test_data:
        value_changer = ValueChanger(data)
        new_function = value_changer.visit(function)
        new_code += astor.to_source(new_function)
    formatted_code = black.format_file_contents(new_code, mode=black.FileMode(), fast=False)
    with open(path_to_out, 'w') as f:
        f.write(formatted_code)
    autoflake._main(['autoflake', '--in-place', '--remove-all-unused-imports', path_to_out], None, None)
    return 0


if __name__ == "__main__":
    test_file_name = os.listdir("/workplace/tests")[0]
    code = open(os.path.join('/workplace/tests', test_file_name)).read()
    code = ast.parse(code)
    tests = discover_tests(code)
    os.makedirs("/tmp/tests", exist_ok=True)
    outs = []
    for test in tests:
        path_to_test_data = f"/workplace/tests_fuzzed_result/{test_file_name[:-3]}_{test}.py/{test_file_name[:-3]}_{test}.py.json"
        if not os.path.exists(path_to_test_data):
            continue
        test_data = json.load(open(path_to_test_data))
        out_path_ = f"/tmp/tests/test_flutils_validators_{test}.py"
        ret = RecreateTests(test, code, test_data, out_path_)
        if ret == 0:
            outs.append(out_path_)
    if len(outs) == 0:
        print("No tests to recreate")
        exit(1)
    final_out = f"/workplace/recreation_results/{test_file_name}"
    with open(final_out, 'w') as f:
        for out in outs:
            f.write(open(out).read())
            f.write("\n")
    


