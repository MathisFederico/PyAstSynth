from typing import Optional, OrderedDict

from astsynth.blanks_and_content import Blank, BlankContent
from astsynth.program import ProgramGraph


class BFSHBrancher:
    """Agent choosing which program blank to fill and with what available content."""

    def choose_blank_candidate(
        self, candidates: OrderedDict[Blank, list[BlankContent]], graph: ProgramGraph
    ) -> tuple[Optional[Blank], Optional[BlankContent]]:
        if graph.empty_blanks:
            choosen_blank = graph.empty_blanks[0]
            if choosen_blank not in candidates:
                return None, None
            return choosen_blank, list(candidates[choosen_blank])[0]
        choosen_blank, blank_candidates = candidates.popitem(last=True)
        return choosen_blank, blank_candidates[0]
