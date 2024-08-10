import ast
from typing import Any, Type

from pydantic import BaseModel, Field

from astsynth.blanks_and_content import Input, Operation, Constant


class DomainSpecificLanguage(BaseModel):
    inputs: list[Input] = Field(default_factory=list)
    constants: list[Constant] = Field(default_factory=list)
    operations: list[Operation] = Field(default_factory=list)

    def load_symbols_from_python_source(self, source: str) -> None:
        module = ast.parse(source)
        exec(compile(module, filename="<ast>", mode="exec"), locals())

        for element in module.body:
            if isinstance(element, ast.Assign):
                if len(element.targets) != 1:
                    raise NotImplementedError
                const_ast_name: ast.Name = element.targets[0]  # type: ignore
                const_ast_value: ast.Constant = element.value  # type: ignore
                new_constant = Constant(
                    name=const_ast_name.id, value=const_ast_value.value
                )
                self.constants.append(new_constant)
            if isinstance(element, ast.FunctionDef):
                input_types = {}
                for arg in element.args.args:
                    if arg.annotation is None:
                        raise ValueError(
                            f"Missing argument type annotation of argument {arg.arg}"
                            f" of function {element.name} in given source"
                        )
                    input_types[arg.arg] = _annotation_to_type(arg.annotation)

                if element.returns is None:
                    raise ValueError(
                        f"Missing return type annotation"
                        f" of function {element.name} in given source"
                    )

                op_start = element.lineno - 1

                if element.end_lineno is None:
                    raise TypeError
                op_end = element.end_lineno + 1

                op_source_lines = source.split("\n")[op_start:op_end]
                new_op = Operation(
                    name=element.name,
                    source="\n".join(op_source_lines),
                    output_type=_annotation_to_type(element.returns),
                    inputs_types=input_types,
                )
                self.operations.append(new_op)


def _annotation_to_type(annotation: ast.expr) -> Type[Any]:
    type_name: ast.Name = annotation  # type: ignore
    return eval(type_name.id)
