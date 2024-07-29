import ast
from astsynth.blanks_and_content import Blank, Variable, VariableKind

from astor import to_source
from networkx import DiGraph


from typing import Type


class ProgramGraph(DiGraph):
    def __init__(
        self, incoming_graph_data=None, output_type: Type[object] = object, **attr
    ):
        super().__init__(incoming_graph_data, **attr)
        self.root = Blank(id="return", type=output_type)
        self.empty_blanks: list[Blank] = [self.root]
        self.add_node(self.root, depth=1)

    def fill_blank(self, blank: Blank, variable: Variable):
        self.add_node(variable, depth=0)
        self.add_edge(blank, variable, active=True)
        self.empty_blanks.remove(blank)

    def empty_blank(self, blank: Blank):
        for succ in self.successors(blank):
            self.edges[blank, succ]["active"] = False
        self.empty_blanks.append(blank)

    def replace_blank(self, blank: Blank, variable: Variable):
        self.empty_blank(blank)
        self.fill_blank(blank, variable)

    @property
    def blanks(self) -> list[Blank]:
        return [node for node in self.nodes() if isinstance(node, Blank)]

    @property
    def complete(self) -> bool:
        return len(self.empty_blanks) == 0


class ProgramWritter:
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
        self.constants.sort(key=lambda c: c.targets[0].id)

        self.inputs_arguments = [
            ast.arg(name, annotation=ast.Name(value.type.__name__))
            for name, value in inputs.items()
        ]

        self.graph = program_graph

    def _blank_filled_ast(self, blank: Blank):
        blank_active_childs = [
            child
            for child in self.graph.successors(blank)
            if self.graph.edges[blank, child]["active"]
        ]
        assert len(blank_active_childs) == 1, "Blank should have only one active child"
        variable_or_op = blank_active_childs.pop()
        if not isinstance(variable_or_op, Variable):
            raise NotImplementedError

        return [ast.Return(ast.Name(variable_or_op.name))]

    def generate_ast(self):
        function_body = self._blank_filled_ast(self.graph.root)

        function = ast.FunctionDef(
            name="generated_func",
            body=function_body,
            decorator_list=[],
            args=ast.arguments(args=self.inputs_arguments, defaults=[]),
        )

        return ast.Module(body=self.constants + [function])

    def __repr__(self) -> str:
        return to_source(self.generate_ast())
