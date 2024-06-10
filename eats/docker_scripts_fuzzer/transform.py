import ast
import os
import typing
from ast import Load

import astor
import autoflake
import black


def has_decorator(func, decorator_name):

    for decorator in func.decorator_list:
        if isinstance(decorator, ast.Call) and \
           isinstance(decorator.func, ast.Attribute):
            if decorator.func.attr == decorator_name:
                return True
    return False


def transform_import(tree):
    import_statements = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_statements.append(node)

    tree.body = [node for node in tree.body if not isinstance(node, (ast.Import, ast.ImportFrom))]

    with_statement = ast.With(
        items=[ast.withitem(context_expr=ast.Call(
            func=ast.Attribute(
                value=ast.Name(id='atheris', ctx=ast.Load()),
                attr='instrument_imports',
                ctx=ast.Load()
            ),
            args=[],
            keywords=[]
        ))],
        body=import_statements
    )
    return with_statement
    

class FunctionTransformer(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        if node.name.startswith("test_"):
            node.args.args.append(ast.arg(arg='data', annotation=None))
            fdp_assignment = ast.Assign(
                targets=[ast.Name(id='fdp', ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id='atheris', ctx=ast.Load()), attr='FuzzedDataProvider', ctx=ast.Load()),
                    args=[ast.Name(id='data', ctx=ast.Load())],
                    keywords=[]
                )
            )
            node.body.insert(0, fdp_assignment)
        return node


def discover_tests(tree):
    function_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if has_decorator(node, "xfail"):
                continue
            function_names.append(node.name)
    return function_names


def create_value_for_type(type_name):
    type_to_attr = {
        'int': 'ConsumeInt',
        'float': 'ConsumeRegularFloat',
        'str': 'ConsumeString',
        # 'bytes': 'ConsumeBytes',
        'bool': 'ConsumeBool',
    }
    type_no_args = ['float', 'bool']
    args = [ast.Constant(value=50)]
    if type_name in type_no_args:
        args = []
    new_value = None
    if type_name in type_to_attr:
        new_value = ast.Call(func=ast.Attribute(value=ast.Name(id='fdp', ctx=Load()), 
                                                attr=type_to_attr[type_name], ctx=Load()),
                             args=args,
                             keywords=[])
    return new_value


class TestTransformer(ast.NodeTransformer):
    should_ignore = False
    node_const: typing.List[typing.Tuple] = None

    def create_fuzz_reader(self):
        body = [
            ast.Assign(
                targets=[ast.Name(id='fdp', ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id='atheris', ctx=ast.Load()), 
                                       attr='FuzzedDataProvider', ctx=ast.Load()),
                    args=[ast.Name(id='data', ctx=ast.Load())],
                    keywords=[]
                )
            )
        ]
        for id, v in self.node_const:
            body.append(ast.Assign(
                targets=[ast.Name(id=id, ctx=ast.Store())],
                value=v
            ))
        body += [
            ast.Assign(
                targets=[ast.Name(id='data', ctx=ast.Store())],
                value=ast.Dict(keys=[ast.Constant(value=k) for k, _ in self.node_const], 
                               values=[ast.Name(id=k, ctx=ast.Load()) for k, _ in self.node_const])
            ),
            ast.Return(
                value=ast.Name(id='data', ctx=ast.Store())
            )
        ]

        func_def = ast.FunctionDef(
            name="fuzz_reader",
            args=ast.arguments(
                args=[ast.arg(arg="data", annotation=None)],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[]
            ),
            body=body,
            decorator_list=[]
        )

        return func_def

    def visit_FunctionDef(self, node):
        if node.name.startswith("test_"):
            self.node_const = []
            # If function starts with "test_", traverse its body and apply transformation
            stmts = [self.visit(stmt) for stmt in node.body]
            const_nodes = []
            other_nodes = []
            for stmt in stmts:
                if isinstance(stmt, ast.Assign):
                    if stmt.targets[0].id in [x for x, _ in self.node_const]:
                        const_nodes.append(stmt)
                    else:
                        other_nodes.append(stmt)
                else:
                    other_nodes.append(stmt)

            except_handler = ast.ExceptHandler(
                type=ast.Name(id='Exception', ctx=ast.Load()),
                name=ast.Name(id='e', ctx=ast.Store()),
                body=[ast.Pass()]
            )
            node.body = [ast.Try(
                body=const_nodes + other_nodes,
                handlers=[except_handler],
                orelse=[],
                finalbody=[]
            )]
            if len(self.node_const) == 0:
                self.should_ignore = True
        return node

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name) and (isinstance(node.value, ast.Constant)):
            type_name = type(node.value.value).__name__
            new_value = create_value_for_type(type_name)
            if new_value:
                node.value = new_value
                self.node_const.append((node.targets[0].id, new_value))
        return node


class AssertRemover(ast.NodeTransformer):
    def visit_Assert(self, node):
        return []

    def visit_With(self, node):
        for item in node.items:
            if (isinstance(item.context_expr, ast.Call) and
                    isinstance(item.context_expr.func, ast.Attribute) and
                    item.context_expr.func.attr == 'raises'):
                return node.body
        return self.generic_visit(node)


def create_main_function(test_name, imports):
    template = f"""
if __name__ == "__main__":
    atheris.Setup(sys.argv, {test_name})
    atheris.Fuzz()
    """
    tree = ast.parse(template)
    tree.body[0].body.insert(0, imports)
    return tree


def transform_code(in_path, out_path):
    out_paths = []
    code = open(in_path, 'br').read()
    parsed_code = ast.parse(code)
    tests = discover_tests(parsed_code)
    for test in tests:
        parsed_code = ast.parse(code)
        new_body = [node for node in parsed_code.body if not isinstance(node, ast.FunctionDef) or node.name == test]
        parsed_code.body = new_body

        import_statement = ast.Import(names=[ast.alias(name='sys', asname=None)])
        parsed_code.body.insert(0, import_statement)

        imports = transform_import(parsed_code)

        import_statement = ast.Import(names=[ast.alias(name='atheris', asname=None)])
        parsed_code.body.insert(0, import_statement)

        transformer = AssertRemover()
        parsed_code = transformer.visit(parsed_code)

        transformer = TestTransformer()
        parsed_code = transformer.visit(parsed_code)
        if transformer.should_ignore:
            continue
        fuzz_reader = transformer.create_fuzz_reader()

        transformer = FunctionTransformer()
        parsed_code = transformer.visit(parsed_code)
        new_code = astor.to_source(parsed_code)
        new_code += astor.to_source(fuzz_reader)
        new_code += astor.to_source(create_main_function(test, imports))
        formatted_code = black.format_file_contents(new_code, mode=black.FileMode(), fast=False)
        out_path_ = os.path.join(out_path, os.path.basename(in_path)[:-3] + "_" + test + ".py")
        with open(out_path_, 'w') as f:
            f.write(formatted_code)
        autoflake._main(['autoflake', '--in-place', '--remove-all-unused-imports', out_path_], None, None)
        out_paths.append(out_path_)
    return out_paths


if __name__ == "__main__":
    in_path = os.path.join("/workplace/tests", os.listdir("/workplace/tests")[0])
    out_path = "/workplace/tests_transformed"
    print("\n".join(transform_code(in_path, out_path)))
