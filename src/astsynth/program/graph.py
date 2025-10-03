from __future__ import annotations

from typing import Any, NamedTuple, Optional, Type
from networkx import DiGraph, descendants


from astsynth.program.blanks import (
    Blank,
    BlankContent,
    BlanksConfig,
    IfBranching,
    Input,
    Operation,
    Constant,
    ProgramHash,
)


class ProgramGraph(DiGraph):
    """Represent the tree of blanks and their content making the heart of the program."""

    def __init__(
        self,
        incoming_graph_data: dict | None = None,
        output_type: Type[object] = object,
        **attr: Any,
    ) -> None:
        super().__init__(incoming_graph_data, **attr)
        self.root = Blank(id="return", type=output_type)
        self.add_node(self.root, depth=0)

    def fill_blank(self, blank: Blank, content: BlankContent) -> None:
        match content.kind:
            case "input" | "constant":
                return self._fill_with_variable(blank, content)
            case "operation":
                return self._fill_with_operation(blank, content)
            case "if":
                return self._fill_with_if(blank, content)
        raise NotImplementedError()

    def empty_blank(self, blank: Blank) -> None:
        for other_blank in descendants(self, blank):
            self.remove_node(other_blank)

    def content(self, blank: Blank) -> Optional[BlankContent]:
        blank_childs: list[BlankContent] = list(self.successors(blank))
        if not blank_childs:
            return None
        assert len(blank_childs) == 1, "Blank should have only one content"
        leaf_node = blank_childs.pop()
        return self.nodes[leaf_node]["content"]

    def replace_blank(self, blank: Blank, content: BlankContent) -> None:
        if self.content(blank) is not None:
            self.empty_blank(blank)
        self.fill_blank(blank, content)

    def sub_blanks(
        self, blank: Blank, operation: Operation | IfBranching
    ) -> list[Blank]:
        op_node = _node_value(blank, operation)
        return list(self.successors(op_node))

    def _fill_with_variable(self, blank: Blank, variable: Input | Constant) -> None:
        var_node = _node_value(blank, variable)
        self.add_node(var_node, content=variable)
        self.add_edge(blank, var_node)

    def _fill_with_operation(self, blank: Blank, operation: Operation) -> None:
        op_node = _node_value(blank, operation)
        self.add_node(op_node, content=operation)
        self.add_edge(blank, op_node)
        new_depth = self.nodes[blank]["depth"] + 1
        for input_name, input_type in operation.inputs_types.items():
            new_blank = Blank(id=f"{op_node}>{input_name}", type=input_type)
            self.add_node(new_blank, depth=new_depth)
            self.add_edge(op_node, new_blank)

    def _fill_with_if(self, blank: Blank, ifbranching: IfBranching) -> None:
        if_node = _node_value(blank, ifbranching)

        if_sub_blanks = IfBlanks(
            test_expression=Blank(id=f"{if_node}>test", type=bool),
            body=Blank(id=f"{if_node}>body", type=blank.type),
            else_case=Blank(id=f"{if_node}>else", type=blank.type),
        )

        self.add_node(if_node, content=ifbranching, subblanks=if_sub_blanks)
        self.add_edge(blank, if_node)
        new_depth = self.nodes[blank]["depth"] + 1

        self.add_node(if_sub_blanks.test_expression, depth=new_depth)
        self.add_edge(if_node, if_sub_blanks.test_expression)

        self.add_node(if_sub_blanks.body, depth=new_depth)
        self.add_edge(if_node, if_sub_blanks.body)

        self.add_node(if_sub_blanks.else_case, depth=new_depth)
        self.add_edge(if_node, if_sub_blanks.else_case)

    @property
    def blanks(self) -> list[Blank]:
        return [node for node in self.nodes() if isinstance(node, Blank)]

    @property
    def empty_blanks(self) -> list[Blank]:
        return [blank for blank in self.blanks if self.content(blank) is None]

    @property
    def complete(self) -> bool:
        return len(self.empty_blanks) == 0

    def config(self) -> BlanksConfig:
        filled_blanks_content: BlanksConfig = {}
        for blank in self.blanks:
            content = self.content(blank)
            filled_blanks_content[blank] = content
        return filled_blanks_content

    @property
    def hashable_config(self) -> ProgramHash:
        return hashable_config(self.config())

    def __hash__(self) -> int:  # pragma: no cover
        return hash(hashable_config(self.config()))


class IfBlanks(NamedTuple):
    test_expression: Blank
    body: Blank
    else_case: Blank


def if_sub_blanks(graph: ProgramGraph, blank: Blank) -> IfBlanks:
    content = graph.content(blank)
    if not content or content.kind != "if":
        raise ValueError("Blank was expeted to contain an if branching operation")
    return graph.nodes[_node_value(blank, content)]["subblanks"]  # type: ignore


def hashable_config(config: BlanksConfig) -> ProgramHash:
    return tuple([(blank, content) for blank, content in config.items()])


def _node_value(blank: Blank, content: BlankContent) -> str:
    match content.kind:
        case "if":
            return blank.id + ">" + "if"
        case "input" | "constant" | "operation":
            return blank.id + ">" + content.name
    raise NotImplementedError()
