import ast
from typing import Any, Callable, Generator, Optional, Type


from astsynth.brancher import BFSHBrancher
from astsynth.blanks_and_content import Operation, Variable, VariableKind
from astsynth.program import ProgramWritter, ProgramGraph


class ProgramGenerator:
    def __init__(
        self,
        inputs: Optional[dict[str, Type[Any]]] = None,
        allowed_constants: Optional[dict[str, Any]] = None,
        operations: Optional[list[Callable[..., Any]]] = None,
        output_type: Type[object] = object,
        brancher: BFSHBrancher = BFSHBrancher(),
    ) -> None:
        self.variables = {}

        if inputs is None:
            inputs = {}
        for name, var_type in inputs.items():
            self.variables[name] = Variable(
                name=name, type=var_type, kind=VariableKind.INPUT
            )

        if allowed_constants is None:
            allowed_constants = {}
        for name, value in allowed_constants.items():
            self.variables[name] = Variable(
                name=name, value=value, type=type(value), kind=VariableKind.CONSTANT
            )

        self.operations = {}
        if operations is None:
            operations = []
        for op_func in operations:
            operation = Operation.from_func(op_func)
            self.operations[operation.name] = operation

        self.output_type = output_type
        self.brancher = brancher
        self.brancher.variables = list(self.variables.values())

    def enumerate(self) -> Generator[ast.Module, None, None]:
        graph = ProgramGraph(output_type=self.output_type)
        program = ProgramWritter(variables=self.variables, program_graph=graph)

        choosen_blank = self.brancher.choose_blank(graph.blanks)
        while choosen_blank is not None and not self.brancher.exausted:
            while not graph.complete:
                choosen_blank = self.brancher.choose_blank(graph.blanks)
                candidate_variable = self.brancher.choose_variable_for_blank(
                    blank=choosen_blank
                )
                graph.fill_blank(blank=choosen_blank, variable=candidate_variable)
            yield program.generate_ast()

            replaced_blank = self.brancher.choose_blank(graph.blanks)
            replacement_variable = self.brancher.choose_variable_for_blank(
                blank=replaced_blank
            )
            graph.replace_blank(blank=replaced_blank, variable=replacement_variable)
            yield program.generate_ast()
