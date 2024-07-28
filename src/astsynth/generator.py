import ast
from typing import Any, Generator, Optional, Type


from astsynth.brancher import BFSHBrancher
from astsynth.blanks_and_content import Variable, VariableKind
from astsynth.program import Program


class ProgramGenerator:
    def __init__(
        self,
        inputs: Optional[dict[str, Any]] = None,
        allowed_constants: Optional[dict[str, Any]] = None,
        output_type: Type[object] = object,
        brancher: BFSHBrancher = BFSHBrancher(),
    ) -> None:
        self.variables = _to_variables(inputs, variable_type=VariableKind.INPUT)
        self.variables.update(
            _to_variables(allowed_constants, variable_type=VariableKind.CONSTANT)
        )
        self.output_type = output_type
        self.brancher = brancher
        self.brancher.variables = list(self.variables.values())

    def enumerate(self) -> Generator[ast.Module, None, None]:
        program = Program(variables=self.variables, output_type=self.output_type)

        choosen_blank = self.brancher.choose_blank(program.blanks)
        while choosen_blank is not None and not self.brancher.exausted:
            while not program.complete:
                choosen_blank = self.brancher.choose_blank(program.blanks)
                candidate_variable = self.brancher.choose_variable_for_blank(
                    blank=choosen_blank
                )
                program.fill_blank(blank=choosen_blank, variable=candidate_variable)
            yield program.generate_ast()

            replaced_blank = self.brancher.choose_blank(program.blanks)
            replacement_variable = self.brancher.choose_variable_for_blank(
                blank=replaced_blank
            )
            program.replace_blank(blank=replaced_blank, variable=replacement_variable)
            yield program.generate_ast()


def _to_variables(
    var_dict: Optional[dict[str, Any]], variable_type: VariableKind
) -> dict[str, Variable]:
    variables = {}
    if var_dict is None:
        var_dict = {}
    for name, value in var_dict.items():
        variables[name] = Variable(name=name, value=value, kind=variable_type)
    return variables
