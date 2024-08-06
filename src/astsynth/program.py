import ast
from typing import Any, Optional, Sequence, Type
from typing_extensions import Self


from astor import to_source
from networkx import DiGraph, NodeNotFound, descendants


from astsynth.blanks_and_content import (
    Blank,
    BlankContent,
    Operation,
    Variable,
    VariableKind,
)

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
        if isinstance(content, Variable):
            return self._fill_with_variable(blank, content)
        if isinstance(content, Operation):
            return self._fill_with_operation(blank, content)
        raise NotImplementedError()

    def blank_with_id(self, blank_id: str) -> Blank:
        blanks_with_id = [b for b in self.active_blanks if b.id == blank_id]
        if not blanks_with_id:
            raise NodeNotFound("Could not find blank with id: %s", blank_id)
        return blanks_with_id[0]

    def _fill_with_variable(self, blank: Blank, variable: Variable) -> None:
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

    def active(self, node: Blank | BlankContent) -> bool:
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


class ProgramGraphBuilder:
    def __init__(self, output_type: Type[object] = object) -> None:
        self.graph = ProgramGraph(output_type=output_type)

    def with_filled_blank(self, blank: Blank, content: BlankContent) -> Self:
        self.graph.replace_blank(blank, content)
        return self

    def build(self) -> ProgramGraph:
        return self.graph


class ProgramWritter:
    """Convert a program graph to an abstract syntax tree."""

    def __init__(
        self,
        variables: dict[str, Variable],
        program_graph: ProgramGraph,
    ) -> None:
        self.constants: list[ast.Assign] = []
        inputs: dict[str, Variable] = {}
        for name, variable in variables.items():
            if not variable.kind == VariableKind.CONSTANT:
                inputs[name] = variable
                continue
            self.constants.append(
                ast.Assign(targets=[ast.Name(name)], value=ast.Constant(variable.value))
            )

        def _assign_const_id(assign: ast.Assign) -> str:
            target_name: ast.Name = assign.targets[0]  # type: ignore
            return target_name.id

        self.constants.sort(key=_assign_const_id)

        self.inputs_arguments = [
            ast.arg(name, annotation=ast.Name(value.type.__name__))
            for name, value in inputs.items()
        ]

        self.graph = program_graph

    def generate_ast(self):
        function_body = self._root_blank_to_ast_body(self.graph.root, self.graph)

        function = ast.FunctionDef(
            name="generated_func",
            body=function_body,
            decorator_list=[],
            args=ast.arguments(args=self.inputs_arguments, defaults=[]),
        )

        return ast.Module(body=self.constants + [function])

    def _blank_ast_value(
        self, blank: Blank, graph: ProgramGraph, variable_count: int
    ) -> tuple[ast.Name | ast.Call, list[tuple[str, Blank]], int]:
        content = graph.content(blank)
        missing_variables = []
        if isinstance(content, Variable):
            ast_value: ast.Name | ast.Call = ast.Name(content.name)
        if isinstance(content, Operation):
            args_asts: list[ast.expr] = []
            for op_blank in graph.sub_blanks(blank=blank, operation=content):
                op_blank_content = graph.content(op_blank)

                if isinstance(op_blank_content, Variable):
                    args_asts.append(ast.Name(op_blank_content.name))

                if isinstance(op_blank_content, Operation):
                    variable_name = f"x{variable_count}"
                    args_asts.append(ast.Name(variable_name))
                    missing_variables.append((variable_name, op_blank))
                    variable_count += 1
            ast_value = ast.Call(
                func=ast.Name(content.name), args=args_asts, keywords=[]
            )
        return ast_value, missing_variables, variable_count

    def _root_blank_to_ast_body(
        self,
        blank: Blank,
        graph: ProgramGraph,
    ) -> Sequence[ast.Return | ast.Assign]:
        ast_value, missing_variables, variables_count = self._blank_ast_value(
            blank, graph, 0
        )
        ast_lines: list[ast.Return | ast.Assign] = [ast.Return(ast_value)]

        while missing_variables:
            var_name, blank = missing_variables.pop(0)
            ast_value, missing_variables, variables_count = self._blank_ast_value(
                blank, graph, variables_count
            )
            ast_lines.insert(
                0, ast.Assign(targets=[ast.Name(var_name)], value=ast_value)
            )

        return ast_lines

    def __repr__(self) -> str:
        return to_source(self.generate_ast())
