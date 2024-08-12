from abc import ABC, abstractmethod
from typing import Optional, OrderedDict

from astsynth.blanks_and_content import Blank, BlankContent
from astsynth.program.graph import ProgramGraph


class SynthesisAgent(ABC):
    """Agent choosing which program blank to fill and with what available content."""

    @abstractmethod
    def act(
        self, candidates: OrderedDict[Blank, list[BlankContent]], graph: ProgramGraph
    ) -> tuple[Optional[Blank], Optional[BlankContent]]:
        """Agent action in the given context."""


class TopDownBFS(SynthesisAgent):
    """Top down enumeration of all programs

    Simply fill all empty blanks then replace then with the first available option,
    backtracting to the most recent valid program when no more options is avilable.

    """

    def act(
        self, candidates: OrderedDict[Blank, list[BlankContent]], graph: ProgramGraph
    ) -> tuple[Optional[Blank], Optional[BlankContent]]:
        if graph.empty_blanks:
            choosen_blank = graph.empty_blanks[0]
            if choosen_blank not in candidates:
                return None, None
            return choosen_blank, list(candidates[choosen_blank])[0]
        choosen_blank, blank_candidates = candidates.popitem(last=True)
        return choosen_blank, blank_candidates[0]
