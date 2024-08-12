from __future__ import annotations

from typing import Any, Optional, Type


from networkx import DiGraph, NodeNotFound, descendants


from astsynth.blanks_and_content import Blank, BlankContent, Input, Operation, Constant


BlanksConfig = dict[Blank, Optional[BlankContent]]


class ProgramGraph(DiGraph):
    """Represent the tree of blanks and their content making the heart of the program."""

    def __init__(
        self,
        incoming_graph_data: dict = None,
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

    def blank_with_id(self, blank_id: str) -> Blank:
        blanks_with_id = [b for b in self.active_blanks if b.id == blank_id]
        if not blanks_with_id:
            raise NodeNotFound("Could not find blank with id: %s", blank_id)
        return blanks_with_id[0]

    def _fill_with_variable(self, blank: Blank, variable: Input | Constant) -> None:
        var_node = self._value_node(blank, variable)
        self.add_node(var_node, content=variable)
        self.add_edge(blank, var_node, active=True)

    def _fill_with_operation(self, blank: Blank, operation: Operation) -> None:
        op_node = self._value_node(blank, operation)
        self.add_node(op_node, content=operation)
        self.add_edge(blank, op_node, active=True)
        for input_name, input_type in operation.inputs_types.items():
            new_blank_id = ">".join((blank.id, operation.name, input_name))
            new_blank = Blank(id=new_blank_id, type=input_type)
            self.add_node(new_blank, depth=self.nodes[blank]["depth"] + 1)
            self.add_edge(op_node, new_blank, active=True)

    def _value_node(self, blank: Blank, content: BlankContent) -> str:
        return blank.id + ">" + content.name

    def replace_blank(self, blank: Blank, content: BlankContent) -> None:
        if self.content(blank) is not None:
            self.deactivate_blank(blank)
        self.fill_blank(blank, content)

    def deactivate_blank(self, blank: Blank) -> None:
        self._deactivate_single_node(blank)
        for other_blank in descendants(self, blank):
            self._deactivate_single_node(other_blank)

    def _deactivate_single_node(self, node: Blank | str) -> None:
        for succ in self.successors(node):
            self.edges[node, succ]["active"] = False

    def content(self, blank: Blank) -> Optional[BlankContent]:
        blank_active_childs: list[BlankContent] = [
            child
            for child in self.successors(blank)
            if self.edges[blank, child]["active"]
        ]
        if not blank_active_childs:
            return None
        assert len(blank_active_childs) == 1, "Blank should have only one active child"
        leaf_node = blank_active_childs.pop()
        return self.nodes[leaf_node]["content"]

    def sub_blanks(self, blank: Blank, operation: Operation) -> list[Blank]:
        op_node = self._value_node(blank, operation)
        return list(self.successors(op_node))

    def active(self, node: Blank | str) -> bool:
        if node == self.root:
            return True
        return any(self.edges[pred, node]["active"] for pred in self.predecessors(node))

    @property
    def active_blanks(self) -> list[Blank]:
        return [
            node
            for node in self.nodes()
            if isinstance(node, Blank) and self.active(node)
        ]

    @property
    def empty_blanks(self) -> list[Blank]:
        return [blank for blank in self.active_blanks if self.content(blank) is None]

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

        for blank in self.active_blanks:
            if blank in would_be_disabled_blanks:
                continue
            if blank in anticipated_content:
                content: Optional[BlankContent] = anticipated_content[blank]
            else:
                content = self.content(blank)
            filled_blanks_content[blank] = content
        return filled_blanks_content
