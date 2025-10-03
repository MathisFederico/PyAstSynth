from copy import deepcopy
import itertools
from typing import Generator, Sequence, Type

from networkx import DiGraph


from astsynth.agent import (
    EmptySubBlanks,
    JumpToFrontiere,
    SynthAction,
    FillBlanks,
    Stop,
    SynthesisAgent,
    all_constants,
)
from astsynth.program.blanks import (
    Blank,
    BlankContent,
    ProgramHash,
    StandardOperation,
)
from astsynth.dsl import DomainSpecificLanguage
from astsynth.program.graph import ProgramGraph


class ProgramGenerator:
    def __init__(
        self,
        dsl: DomainSpecificLanguage,
        output_type: Type[object],
        agent: SynthesisAgent,
        standard_operations: list[StandardOperation] | None = None,
    ) -> None:
        self.output_type = output_type
        self.agent = agent
        self.dsl = dsl
        if standard_operations is None:
            standard_operations = []
        self.available_contents = (
            list(self.dsl.inputs)
            + list(self.dsl.constants)
            + list(self.dsl.operations)
            + standard_operations
        )

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
                    candidate_contents=self.available_contents,
                    blank=blank,
                    graph=current_graph,
                )
                continue

            match blank_content.kind:
                case "operation" | "if":
                    op_sub_blanks = current_graph.sub_blanks(
                        blank=blank, operation=blank_content
                    )
                    any_sub_blank_has_content = any(
                        current_graph.content(op_blank) for op_blank in op_sub_blanks
                    )
                    if not any_sub_blank_has_content:
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
            depth_increase = 0 if all_constants(action) else 1
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

            available_actions_results[FillBlanks(blanks_contents=blanks_contents)] = (
                would_be_graph
            )

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
    """Exception due to invalid program synthesis configuration"""


def _available_fill_blank_contents(
    candidate_contents: Sequence[BlankContent], blank: Blank, graph: ProgramGraph
) -> list[tuple[Blank, BlankContent]]:
    available_actions: list[tuple[Blank, BlankContent]] = []
    for content in candidate_contents:
        match content.kind:
            case "input" | "constant":
                if not issubclass(content.type, blank.type):
                    continue
            case "operation":
                if not issubclass(content.output_type, blank.type):
                    continue
            case "if":
                # We can always replace a blank by an if branch with the same return type
                # But we avoid having if branches directly within an if
                preds = list(graph.predecessors(blank))
                if len(preds) > 0:
                    pred_blank = list(graph.predecessors(preds[0]))[0]
                    pred_content = graph.content(pred_blank)
                    if pred_content and pred_content.kind == "if":
                        continue
        available_actions.append((blank, content))
    return available_actions
