from astsynth.blanks_and_content import Blank, Constant, Input, Operation
from astsynth.dsl import DomainSpecificLanguage
from astsynth.program import GeneratedProgram
from astsynth.program.graph import ProgramGraph


from astor import to_source


import ast
from typing import Sequence


def graph_to_program(
    graph: ProgramGraph, program_name: str, dsl: DomainSpecificLanguage
) -> GeneratedProgram:
    constants_ast: dict[Constant, ast.Assign] = {}

    for constant in dsl.constants:
        constants_ast[constant] = ast.Assign(
            targets=[ast.Name(constant.name)],
            value=ast.Constant(constant.value),
        )

    inputs_arguments = [
        ast.arg(input_var.name, annotation=ast.Name(input_var.type.__name__))
        for input_var in dsl.inputs
    ]
    operations_ast: dict[Operation, ast.FunctionDef] = {}
    for op in dsl.operations:
        operations_ast[op] = ast.parse(op.source).body[0]  # type: ignore

    active_constants: list[ast.Assign] = []
    active_ops: list[ast.FunctionDef] = []

    for node, content in graph.nodes(data="content"):
        if not graph.active(node):
            continue
        if content in constants_ast:
            active_constants.append(constants_ast[content])
        elif content in operations_ast:
            active_ops.append(operations_ast[content])

    def _assign_const_id(assign: ast.Assign) -> str:
        target_name: ast.Name = assign.targets[0]  # type: ignore
        return target_name.id

    active_constants = sorted(list(set(active_constants)), key=_assign_const_id)
    active_ops = sorted(list(set(active_ops)), key=lambda func_def: func_def.name)

    function_body = _root_blank_to_ast_body(graph.root, graph)

    function = ast.FunctionDef(
        name=program_name,
        body=function_body,
        decorator_list=[],
        args=ast.arguments(args=inputs_arguments, defaults=[]),  # type: ignore
    )

    module = ast.Module(
        body=active_constants + active_ops + [function], type_ignores=[]
    )
    source = to_source(module)
    return GeneratedProgram(name=program_name, source=source)


def _root_blank_to_ast_body(
    blank: Blank,
    graph: ProgramGraph,
) -> Sequence[ast.Return | ast.Assign]:
    ast_value, missing_variables, variables_count = _blank_ast_value(blank, graph, 0)
    ast_lines: list[ast.Return | ast.Assign] = [ast.Return(ast_value)]

    while missing_variables:
        var_name, blank = missing_variables.pop(0)
        ast_value, missing_variables, variables_count = _blank_ast_value(
            blank, graph, variables_count
        )
        ast_lines.insert(0, ast.Assign(targets=[ast.Name(var_name)], value=ast_value))

    return ast_lines


def _blank_ast_value(
    blank: Blank, graph: ProgramGraph, variable_count: int
) -> tuple[ast.Name | ast.Call, list[tuple[str, Blank]], int]:
    content = graph.content(blank)
    missing_variables = []
    if isinstance(content, (Input, Constant)):
        ast_value: ast.Name | ast.Call = ast.Name(content.name)
    if isinstance(content, Operation):
        args_asts: list[ast.expr] = []
        for op_blank in graph.sub_blanks(blank=blank, operation=content):
            op_blank_content = graph.content(op_blank)

            if isinstance(op_blank_content, (Input, Constant)):
                args_asts.append(ast.Name(op_blank_content.name))

            elif isinstance(op_blank_content, Operation):
                variable_name = f"x{variable_count}"
                args_asts.append(ast.Name(variable_name))
                missing_variables.append((variable_name, op_blank))
                variable_count += 1
            else:
                raise NotImplementedError

        ast_value = ast.Call(func=ast.Name(content.name), args=args_asts, keywords=[])
    return ast_value, missing_variables, variable_count
