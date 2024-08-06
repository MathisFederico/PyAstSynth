from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from astsynth.program import ProgramGraph


class ProgramNamer(ABC):
    @abstractmethod
    def name(self, graph: "ProgramGraph") -> str:
        """Name the program from its current graph."""


class DefaultProgramNamer(ProgramNamer):
    def name(self, graph: "ProgramGraph") -> str:
        return "generated_func"
