from __future__ import annotations

from typing import Any, Optional, Type
from networkx import DiGraph, descendants


from astsynth.blanks_and_content import (
    Blank,
    BlankContent,
    BlanksConfig,
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
        if isinstance(content, (Input, Constant)):
            return self._fill_with_variable(blank, content)
        if isinstance(content, Operation):
            return self._fill_with_operation(blank, content)
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

    def sub_blanks(self, blank: Blank, operation: Operation) -> list[Blank]:
        op_node = self._value_node(blank, operation)
        return list(self.successors(op_node))

    def _fill_with_variable(self, blank: Blank, variable: Input | Constant) -> None:
        var_node = self._value_node(blank, variable)
        self.add_node(var_node, content=variable)
        self.add_edge(blank, var_node)

    def _fill_with_operation(self, blank: Blank, operation: Operation) -> None:
        op_node = self._value_node(blank, operation)
        self.add_node(op_node, content=operation)
        self.add_edge(blank, op_node)
        for input_name, input_type in operation.inputs_types.items():
            new_blank_id = ">".join((blank.id, operation.name, input_name))
            new_blank = Blank(id=new_blank_id, type=input_type)
            self.add_node(new_blank, depth=self.nodes[blank]["depth"] + 1)
            self.add_edge(op_node, new_blank)

    def _value_node(self, blank: Blank, content: BlankContent) -> str:
        return blank.id + ">" + content.name

    @property
    def blanks(self) -> list[Blank]:
        return [node for node in self.nodes() if isinstance(node, Blank)]

    @property
    def empty_blanks(self) -> list[Blank]:
        return [blank for blank in self.blanks if self.content(blank) is None]

    @property
    def complete(self) -> bool:
        return len(self.empty_blanks) == 0

    def config(
        self, anticipated_content: Optional[dict[Blank, BlankContent]] = None
    ) -> BlanksConfig:
        if anticipated_content is None:
            anticipated_content = {}
        filled_blanks_content: BlanksConfig = {}

        would_be_disabled_blanks: set[Blank | BlankContent] = set()
        for changed_blank in anticipated_content:
            would_be_disabled_blanks = would_be_disabled_blanks.union(
                [
                    des
                    for des in descendants(self, changed_blank)
                    if isinstance(des, Blank)
                ]
            )

        for blank in self.blanks:
            if blank in would_be_disabled_blanks:
                continue
            if blank in anticipated_content:
                content: Optional[BlankContent] = anticipated_content[blank]
            else:
                content = self.content(blank)
            filled_blanks_content[blank] = content
        return filled_blanks_content

    @property
    def hashable_config(self) -> ProgramHash:
        return hashable_config(self.config())

    def __hash__(self) -> int:  # pragma: no cover
        return hash(hashable_config(self.config()))


def hashable_config(config: BlanksConfig) -> ProgramHash:
    return tuple([(blank, content) for blank, content in config.items()])
