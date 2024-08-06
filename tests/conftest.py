import ast

import astor


def function_ast_from_source_lines(source_lines: list[str]) -> ast.Module:
    return ast.parse("\n".join(source_lines))


def to_source_list(asts: list[ast.Module]) -> list[str]:
    return [astor.to_source(tree) for tree in asts]
