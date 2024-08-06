import ast
from collections import OrderedDict
from functools import partial
from typing import Any, Callable, Generator, Iterator, Optional, Type


from astsynth.brancher import BFSHBrancher
from astsynth.blanks_and_content import (
    Blank,
    BlankContent,
    Operation,
    Variable,
    VariableKind,
)
from astsynth.program import BlanksConfig, ProgramWritter, ProgramGraph


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
        self.candidates = list(self.variables.values()) + list(self.operations.values())

    def enumerate(self, max_depth: int = 1) -> Generator[ast.Module, None, None]:
        graph = ProgramGraph(output_type=self.output_type)
        program = ProgramWritter(variables=self.variables, program_graph=graph)

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
            choosen_blank, candidate = self.brancher.choose_blank_candidate(
                blanks_candidates, graph
            )
            if choosen_blank is None or candidate is None:
                # Exaustion
                return
            graph.replace_blank(blank=choosen_blank, content=candidate)
            if graph.complete:
                complete_config = graph.config()
                used_configs.add(hashable_config(complete_config))
                yield program.generate_ast()
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
    candidates: list[BlankContent] | Iterator[BlankContent],
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
    if isinstance(content, Variable):
        return issubclass(content.type, blank.type)
    if isinstance(content, Operation):
        return issubclass(content.output_type, blank.type)
    raise NotImplementedError
