from astsynth.program.blanks import Blank, BlankContent, Constant, Operation
from astsynth.dsl import DomainSpecificLanguage
from astsynth.program import GeneratedProgram
from astsynth.program.graph import ProgramGraph, if_sub_blanks


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

    for _node, content in graph.nodes(data="content"):
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
        body=active_constants + active_ops + [function],  # pyright: ignore
        type_ignores=[],
    )
    source = to_source(module)
    return GeneratedProgram(name=program_name, source=source)


def _root_blank_to_ast_body(
    blank: Blank,
    graph: ProgramGraph,
) -> Sequence[ast.Return | ast.Assign | ast.If]:
    ast_value, missing_variables, variables_count = _blank_ast_value(blank, graph, 0)
    ast_lines: list[ast.Return | ast.Assign | ast.If] = []
    if isinstance(ast_value, (ast.Name, ast.Call)):
        ast_lines.append(ast.Return(ast_value))
    else:
        ast_lines.append(ast_value)

    while missing_variables:
        var_name, blank = missing_variables.pop(0)
        ast_value, new_missing_variables, variables_count = _blank_ast_value(
            blank, graph, variables_count
        )
        missing_variables += new_missing_variables
        ast_lines.insert(0, ast.Assign(targets=[ast.Name(var_name)], value=ast_value))  # type: ignore

    return ast_lines


def _blank_ast_value(
    blank: Blank, graph: ProgramGraph, variable_count: int
) -> tuple[ast.Name | ast.Call | ast.If, list[tuple[str, Blank]], int]:
    content = graph.content(blank)
    if content is None:
        raise TypeError("Cannot represent the ast value of an empty blank")
    missing_variables = []

    def _refer_to_subblank_variable_name(
        subblank: Blank, subcontent: BlankContent
    ) -> str:
        match subcontent.kind:
            case "input" | "constant":
                return subcontent.name
            case "operation":
                variable_name = f"x{variable_count}"
                missing_variables.append((variable_name, subblank))
                return variable_name
        raise NotImplementedError

    match content.kind:
        case "input" | "constant":
            ast_value: ast.Name | ast.Call | ast.If = ast.Name(content.name)
        case "operation":
            args_asts: list[ast.expr] = []
            for op_blank in graph.sub_blanks(blank=blank, operation=content):
                op_blank_content = graph.content(op_blank)
                if op_blank_content is None:
                    raise TypeError("Cannot represent the ast value of an empty blank")
                var_name = _refer_to_subblank_variable_name(op_blank, op_blank_content)
                args_asts.append(ast.Name(var_name))
            ast_value = ast.Call(
                func=ast.Name(content.name), args=args_asts, keywords=[]
            )
        case "if":
            sub_blanks = if_sub_blanks(graph, blank)
            test_content = graph.content(sub_blanks.test_expression)
            if test_content is None:
                raise TypeError("Cannot represent the ast value of an empty blank")
            body_content = graph.content(sub_blanks.body)
            if body_content is None:
                raise TypeError("Cannot represent the ast value of an empty blank")
            else_content = graph.content(sub_blanks.else_case)
            if else_content is None:
                raise TypeError("Cannot represent the ast value of an empty blank")
            ast_value = ast.If(
                test=ast.Name(
                    _refer_to_subblank_variable_name(
                        sub_blanks.test_expression, test_content
                    )
                ),
                body=[
                    ast.Return(
                        ast.Name(
                            _refer_to_subblank_variable_name(
                                sub_blanks.body, body_content
                            )
                        )
                    )
                ],
                orelse=[
                    ast.Return(
                        ast.Name(
                            _refer_to_subblank_variable_name(
                                sub_blanks.else_case, else_content
                            )
                        )
                    )
                ],
            )
        case _:  # pragma: no cover
            raise TypeError(f"Unsupported type: {type(content)}")
    return ast_value, missing_variables, variable_count + len(missing_variables)
