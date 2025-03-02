import ast
from pathlib import Path
from typing import TYPE_CHECKING, Any, Type

from pydantic import BaseModel, Field

from astsynth.blanks_and_content import Input, Operation, Constant

if TYPE_CHECKING:
    from astsynth.task import Task


class DomainSpecificLanguage(BaseModel):
    inputs: list[Input] = Field(default_factory=list)
    constants: list[Constant] = Field(default_factory=list)
    operations: list[Operation] = Field(default_factory=list)

    def add_task_inputs(self, task: "Task") -> None:
        self.inputs += [
            Input(name=name, type=type) for name, type in task.input_types.items()
        ]

    def augment(self, other: "DomainSpecificLanguage") -> None:
        _check_empty_intersection(self.inputs, other.inputs)
        _check_empty_intersection(self.constants, other.constants)
        _check_empty_intersection(self.operations, other.operations)
        self.inputs += other.inputs
        self.constants += other.constants
        self.operations += other.operations


def _check_empty_intersection(list_a: list, list_b: list) -> None:
    common_inputs = set(list_a).intersection(set(list_b))
    if common_inputs:
        raise ValueError(
            f"Cannot augment with a conflicting DSL. Conflics: {common_inputs}"
        )


def load_symbols_from_python_source(source: str) -> DomainSpecificLanguage:
    module = ast.parse(source)
    exec(compile(module, filename="<ast>", mode="exec"), locals())

    constants: list[Constant[Any]] = []
    operations: list[Operation] = []

    for element in module.body:
        if isinstance(element, ast.Assign):
            if len(element.targets) != 1:
                raise NotImplementedError
            const_ast_name: ast.Name = element.targets[0]  # type: ignore
            const_ast_value: ast.Constant = element.value  # type: ignore
            new_constant: Constant[Any] = Constant(
                name=const_ast_name.id, value=const_ast_value.value
            )
            constants.append(new_constant)
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
            operations.append(new_op)

    return DomainSpecificLanguage(constants=constants, operations=operations)


def load_symbols_from_python_file(filepath: Path) -> DomainSpecificLanguage:
    return load_symbols_from_python_source(filepath.read_text())


def _annotation_to_type(annotation: ast.expr) -> Type[Any]:
    type_name: ast.Name = annotation  # type: ignore
    return eval(type_name.id)
