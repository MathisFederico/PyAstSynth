from copy import deepcopy
import itertools
from typing import Generator, Type

from networkx import DiGraph


from astsynth.agent import (
    EmptySubBlanks,
    JumpToFrontiere,
    SynthAction,
    FillBlanks,
    Stop,
    SynthesisAgent,
    all_const,
)
from astsynth.program.blanks import (
    Blank,
    BlankContent,
    Input,
    Operation,
    Constant,
    ProgramHash,
)
from astsynth.dsl import DomainSpecificLanguage
from astsynth.program.graph import ProgramGraph


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
        non_ops = list(self.dsl.inputs) + list(self.dsl.constants)
        self.contents = non_ops + list(self.dsl.operations)

    def enumerate(self, max_depth: int) -> Generator[ProgramGraph, None, None]:
        current_graph = ProgramGraph(output_type=self.output_type)

        programs_graph = DiGraph()
        programs_graph.add_node(
            current_graph.hashable_config,
            explored=False,
            depth=0,
            program_graph=current_graph,
        )

        frontiere: dict[ProgramHash, ProgramGraph] = {
            current_graph.hashable_config: current_graph
        }
        actions_consequences: dict[SynthAction, ProgramGraph] = self._update_frontiere(
            frontiere=frontiere,
            programs_graph=programs_graph,
            current_graph=current_graph,
            max_depth=max_depth,
        )

        if not actions_consequences:
            raise SynthesisError(
                f"Could not find any way to generate output type: {self.output_type}"
            )

        done = False
        while not done:
            action = self.agent.act(
                candidates=list(actions_consequences.keys()),
                graph=current_graph,
            )

            done = isinstance(action, Stop)
            if done:
                return

            current_graph = actions_consequences[action]
            if current_graph.complete:
                yield current_graph

            actions_consequences = self._update_frontiere(
                frontiere=frontiere,
                programs_graph=programs_graph,
                current_graph=current_graph,
                max_depth=max_depth,
            )

    def _update_frontiere(
        self,
        frontiere: dict[ProgramHash, ProgramGraph],
        programs_graph: DiGraph,
        current_graph: ProgramGraph,
        max_depth: int,
    ) -> dict[SynthAction, ProgramGraph]:
        current_config = current_graph.hashable_config
        programs_graph.nodes[current_config]["explored"] = True
        current_depth = programs_graph.nodes[current_config]["depth"]
        if current_config in frontiere:
            frontiere.pop(current_config)
        available_actions_results: dict[SynthAction, ProgramGraph] = {}

        fill_blank_options: dict[Blank, list[tuple[Blank, BlankContent]]] = {}
        for blank in current_graph.blanks:
            blank_content = current_graph.content(blank)
            if blank_content is None:
                fill_blank_options[blank] = _available_fill_blank_contents(
                    candidate_contents=self.contents, blank=blank, graph=current_graph
                )
                continue

            if isinstance(blank_content, Operation):
                op_sub_blanks = current_graph.sub_blanks(
                    blank=blank, operation=blank_content
                )
                if not any(
                    current_graph.content(op_blank) for op_blank in op_sub_blanks
                ):
                    continue

                action: SynthAction = EmptySubBlanks(
                    parent_blank=blank,
                    blanks=tuple(op_sub_blanks),
                )
                would_be_graph = deepcopy(current_graph)
                for op_blank in op_sub_blanks:
                    would_be_graph.empty_blank(blank=op_blank)
                available_actions_results[action] = would_be_graph
                continue

            if blank.id == "return":
                empty_return_action: SynthAction = EmptySubBlanks(blanks=(blank,))
                would_be_graph = deepcopy(current_graph)
                would_be_graph.empty_blank(blank=blank)
                available_actions_results[empty_return_action] = would_be_graph
                continue

        for blanks_contents in itertools.product(*fill_blank_options.values()):
            action = FillBlanks(blanks_contents=blanks_contents)
            depth_increase = 0 if all_const(action) else 1
            would_be_graph = deepcopy(current_graph)
            for blank, content in blanks_contents:
                would_be_graph.fill_blank(blank=blank, content=content)

            would_be_config = would_be_graph.hashable_config
            would_be_depth = current_depth + depth_increase
            if would_be_config in programs_graph:
                pred_depths_p1 = [
                    programs_graph.nodes[pred]["depth"] + 1
                    for pred in programs_graph.predecessors(would_be_config)
                ]
                would_be_depth = min([would_be_depth] + pred_depths_p1)
                programs_graph.nodes[would_be_config]["depth"] = would_be_depth

            if would_be_depth > max_depth:
                continue

            if would_be_config not in programs_graph:
                programs_graph.add_node(
                    would_be_config,
                    explored=False,
                    depth=would_be_depth,
                    program_graph=would_be_graph,
                )
                if not would_be_graph.complete:
                    frontiere[would_be_config] = would_be_graph

            programs_graph.add_edge(current_config, would_be_config, action=action)
            if programs_graph.nodes[would_be_config]["explored"]:
                continue

            available_actions_results[
                FillBlanks(blanks_contents=blanks_contents)
            ] = would_be_graph

        for config, graph in frontiere.items():
            if programs_graph.nodes[config]["depth"] > max_depth:  # pragma: no cover
                continue
            if config in [
                g.hashable_config for g in available_actions_results.values()
            ]:
                continue
            available_actions_results[JumpToFrontiere(config=config)] = graph

        available_actions_results[Stop()] = current_graph
        return available_actions_results


class SynthesisError(Exception):
    """Exception due to invalid program synsthesis configuration"""


def _available_fill_blank_contents(
    candidate_contents: list[BlankContent], blank: Blank, graph: ProgramGraph
) -> list[tuple[Blank, BlankContent]]:
    available_actions: list[tuple[Blank, BlankContent]] = []
    for content in candidate_contents:
        if not _match_type(blank=blank, content=content):
            continue
        available_actions.append((blank, content))
    return available_actions


def _match_type(blank: Blank, content: BlankContent) -> bool:
    if isinstance(content, (Input, Constant)):
        return issubclass(content.type, blank.type)
    if isinstance(content, Operation):
        return issubclass(content.output_type, blank.type)
    raise NotImplementedError
