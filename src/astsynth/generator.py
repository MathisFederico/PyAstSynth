from collections import OrderedDict
from functools import partial
from typing import Generator, Iterator, Optional, Type


from astsynth.agent import SynthesisAgent
from astsynth.blanks_and_content import Blank, BlankContent, Input, Operation, Constant
from astsynth.dsl import DomainSpecificLanguage
from astsynth.namer import DefaultProgramNamer, ProgramNamer
from astsynth.program import GeneratedProgram
from astsynth.program.graph import BlanksConfig, ProgramGraph
from astsynth.program.writter import graph_to_program


class ProgramGenerator:
    def __init__(
        self,
        dsl: DomainSpecificLanguage,
        output_type: Type[object],
        agent: SynthesisAgent,
    ) -> None:
        self.output_type = output_type
        self.agent = agent
        self.dsl = dsl
        self.candidates = (
            list(self.dsl.inputs) + list(self.dsl.constants) + list(self.dsl.operations)
        )

    def enumerate(
        self,
        max_depth: int,
        program_namer: Optional[ProgramNamer] = None,
    ) -> Generator[GeneratedProgram, None, None]:
        graph = ProgramGraph(output_type=self.output_type)

        if program_namer is None:
            program_namer = DefaultProgramNamer()

        blanks_candidates: OrderedDict[Blank, list[BlankContent]] = OrderedDict()
        root_candidates = list(
            candidates(
                self.candidates, blank=graph.root, graph=graph, max_depth=max_depth
            )
        )
        if not root_candidates:
            raise SynthesisError(
                f"Could not find any way to generate output type: {self.output_type}"
            )
        blanks_candidates[graph.root] = root_candidates
        used_configs = set()
        while blanks_candidates:
            choosen_blank, candidate = self.agent.act(blanks_candidates, graph)
            if choosen_blank is None or candidate is None:
                # Exaustion
                return
            graph.replace_blank(blank=choosen_blank, content=candidate)
            if graph.complete:
                complete_config = graph.config()
                program_name = program_namer.name(graph)
                used_configs.add(hashable_config(complete_config))
                yield graph_to_program(
                    program_name=program_name, graph=graph, dsl=self.dsl
                )
            blanks_candidates = update_current_candidates(
                graph=graph,
                all_candidates=self.candidates,
                used_configs=used_configs,
                max_depth=max_depth,
            )


class SynthesisError(Exception):
    """Exception due to invalid program synsthesis configuration"""


HashedConfig = tuple[tuple[Blank, Optional[BlankContent]], ...]


def hashable_config(config: BlanksConfig) -> HashedConfig:
    return tuple([(blank, content) for blank, content in config.items()])


def update_current_candidates(
    graph: ProgramGraph,
    all_candidates: list[BlankContent],
    used_configs: set[HashedConfig],
    max_depth: int,
) -> OrderedDict[Blank, list[BlankContent]]:
    blanks_candidates: OrderedDict[Blank, list[BlankContent]] = OrderedDict()
    for blank in graph.active_blanks:
        blank_candidates = []
        for new_candidate in candidates(
            all_candidates, blank=blank, graph=graph, max_depth=max_depth
        ):
            if new_candidate == graph.content(blank):
                continue
            would_be_config = graph.config({blank: new_candidate})
            if hashable_config(would_be_config) in used_configs:
                continue
            blank_candidates.append(new_candidate)
        if blank_candidates:
            blanks_candidates[blank] = blank_candidates
    return blanks_candidates


def candidates(
    candidates: list[BlankContent],
    blank: Blank,
    graph: ProgramGraph,
    max_depth: int,
) -> Iterator[BlankContent]:
    return filter(
        partial(is_valid_candidate, graph=graph, blank=blank, max_depth=max_depth),
        candidates,
    )


def is_valid_candidate(
    candidate: BlankContent, graph: ProgramGraph, blank: Blank, max_depth: int
) -> bool:
    if not match_type(blank=blank, content=candidate):
        return False
    if isinstance(candidate, Operation) and graph.nodes[blank]["depth"] >= max_depth:
        return False
    return True


def match_type(blank: Blank, content: BlankContent) -> bool:
    if isinstance(content, (Input, Constant)):
        return issubclass(content.type, blank.type)
    if isinstance(content, Operation):
        return issubclass(content.output_type, blank.type)
    raise NotImplementedError
