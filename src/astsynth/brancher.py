from typing import Optional
from astsynth.blanks_and_content import Blank, Variable


class BFSHBrancher:
    def __init__(self) -> None:
        self._next_variables = None
        self.variables: list[Variable] = []
        self.used_variables: dict[Blank, list[Variable]] = {}

    def choose_blank(self, available_blanks: list[Blank]) -> Optional[Blank]:
        for blank in available_blanks:
            if blank not in self.used_variables:
                self.used_variables[blank] = []
        return available_blanks[0]

    def choose_variable_for_blank(self, blank: Blank) -> Variable:
        for canditate_variable in self.variables:
            if not issubclass(canditate_variable.type, blank.type):
                continue
            if canditate_variable in self.used_variables[blank]:
                continue
            self.used_variables[blank].append(canditate_variable)
            return canditate_variable

    @property
    def exausted(self) -> bool:
        blanks_exausted = {}
        for blank, used_variables in self.used_variables.items():
            possibilities = set(
                var for var in self.variables if issubclass(var.type, blank.type)
            )
            blanks_exausted[blank] = set(used_variables) == possibilities

        return all(blanks_exausted.values())
