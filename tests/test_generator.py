import ast
from difflib import Differ
import json
from typing import Any, Callable, Type
import pytest

from astsynth.program.blanks import (
    IfBranching,
    Input,
    Operation,
    Constant,
    StandardOperation,
)
from astsynth.agent import SynthesisAgent, TopDownBFS
from astsynth.dsl import DomainSpecificLanguage
from astsynth.generator import ProgramGenerator

from astsynth.program.writter import graph_to_program
from tests.conftest import function_ast_from_source_lines, to_source_list


class TestGeneration:
    @pytest.fixture(autouse=True)
    def setup(self, generation_fixture: "CodeGenerationFixture") -> None:
        self.fixture = generation_fixture

    def test_return_variable(self):
        """should be able to simply return variables (of the expected type) whether variables are constants or inputs."""
        self.fixture.given_program_inputs({"number": int, "desc": str})
        self.fixture.given_program_constants({"N": 42, "A": "a constant string"})
        self.fixture.given_output_type(int)
        self.fixture.given_agent(TopDownBFS())

        self.fixture.when_enumerating_generation(max_depth=0)
        self.fixture.then_generated_functions_asts_should_be(
            [
                # Depth 0
                function_ast_from_source_lines(
                    [
                        "def generated_func(number: int, desc: str):",
                        "    return number",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        "N = 42",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return N",
                    ]
                ),
            ]
        )

    def test_if_branching(self):
        """should be able to simply return variables (of the expected type) whether variables are constants or inputs."""

        def is_even(number: int) -> bool:
            return number % 2 == 0

        self.fixture.given_program_inputs({"number": int})
        self.fixture.given_program_constants({"EVEN": "even", "ODD": "odd"})
        self.fixture.given_program_operations([is_even])
        self.fixture.given_program_standard_operations([IfBranching()])
        self.fixture.given_output_type(str)
        self.fixture.given_agent(TopDownBFS())

        self.fixture.when_enumerating_generation(max_depth=2)
        self.fixture.then_generated_functions_asts_should_be(
            [
                # Depth 0
                function_ast_from_source_lines(
                    [
                        'EVEN = "even"',
                        "",
                        "def generated_func(number: int):",
                        "    return EVEN",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        'ODD = "odd"',
                        "",
                        "def generated_func(number: int):",
                        "    return ODD",
                    ]
                ),
                # Depth 2
                function_ast_from_source_lines(
                    [
                        'EVEN = "even"',
                        "",
                        "def is_even(number: int) -> bool:",
                        "    return number % 2 == 0",
                        "",
                        "",
                        "def generated_func(number: int):",
                        "    x0 = is_even(number)",
                        "    if x0:",
                        "        return EVEN",
                        "    else:",
                        "        return EVEN",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        'EVEN = "even"',
                        'ODD = "odd"',
                        "",
                        "def is_even(number: int) -> bool:",
                        "    return number % 2 == 0",
                        "",
                        "",
                        "def generated_func(number: int):",
                        "    x0 = is_even(number)",
                        "    if x0:",
                        "        return EVEN",
                        "    else:",
                        "        return ODD",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        'EVEN = "even"',
                        'ODD = "odd"',
                        "",
                        "def is_even(number: int) -> bool:",
                        "    return number % 2 == 0",
                        "",
                        "",
                        "def generated_func(number: int):",
                        "    x0 = is_even(number)",
                        "    if x0:",
                        "        return ODD",
                        "    else:",
                        "        return EVEN",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        'ODD = "odd"',
                        "",
                        "def is_even(number: int) -> bool:",
                        "    return number % 2 == 0",
                        "",
                        "",
                        "def generated_func(number: int):",
                        "    x0 = is_even(number)",
                        "    if x0:",
                        "        return ODD",
                        "    else:",
                        "        return ODD",
                    ]
                ),
            ]
        )

    def test_operation_on_variables(self):
        def concat_strings(string: str, other_string: str) -> str:
            return string + other_string

        def repeat(string: str, times: int) -> str:
            return string * times

        self.fixture.given_program_inputs({"number": int, "desc": str})
        self.fixture.given_program_constants({"A": "a"})
        self.fixture.given_program_operations([concat_strings, repeat])
        self.fixture.given_output_type(str)
        self.fixture.given_agent(TopDownBFS())

        self.fixture.when_enumerating_generation(max_depth=1)
        self.fixture.then_generated_functions_asts_should_be(
            [
                # Depth 1
                function_ast_from_source_lines(
                    [
                        "def generated_func(number: int, desc: str):",
                        "    return desc",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        'A = "a"',
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return A",
                    ]
                ),
                # Depth 2
                function_ast_from_source_lines(
                    [
                        "def concat_strings(string: str, other_string: str) -> str:",
                        "   return string + other_string",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return concat_strings(desc, desc)",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        'A = "a"',
                        "",
                        "def concat_strings(string: str, other_string: str) -> str:",
                        "   return string + other_string",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return concat_strings(desc, A)",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        'A = "a"',
                        "",
                        "def concat_strings(string: str, other_string: str) -> str:",
                        "   return string + other_string",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return concat_strings(A, desc)",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        'A = "a"',
                        "",
                        "def concat_strings(string: str, other_string: str) -> str:",
                        "   return string + other_string",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return concat_strings(A, A)",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        "def repeat(string: str, times: int) -> str:",
                        "   return string * times",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return repeat(desc, number)",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        'A = "a"',
                        "",
                        "def repeat(string: str, times: int) -> str:",
                        "   return string * times",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return repeat(A, number)",
                    ]
                ),
            ]
        )

    def test_depth_makes_intermediate_variables(self):
        def add_one(number: int) -> int:
            return number + 1

        self.fixture.given_program_inputs({"number": int})
        self.fixture.given_program_operations([add_one])
        self.fixture.given_output_type(int)
        self.fixture.given_agent(TopDownBFS())

        self.fixture.when_enumerating_generation(max_depth=3)
        self.fixture.then_generated_functions_asts_should_be(
            [
                # Depth 0
                function_ast_from_source_lines(
                    [
                        "def generated_func(number: int):",
                        "    return number",
                    ]
                ),
                # Depth 1
                function_ast_from_source_lines(
                    [
                        "def add_one(number: int) -> int:",
                        "   return number + 1",
                        "",
                        "def generated_func(number: int):",
                        "    return add_one(number)",
                    ]
                ),
                # Depth 2
                function_ast_from_source_lines(
                    [
                        "def add_one(number: int) -> int:",
                        "   return number + 1",
                        "",
                        "def generated_func(number: int):",
                        "    x0 = add_one(number)",
                        "    return add_one(x0)",
                    ]
                ),
                # Depth 3
                function_ast_from_source_lines(
                    [
                        "def add_one(number: int) -> int:",
                        "   return number + 1",
                        "",
                        "def generated_func(number: int):",
                        "    x1 = add_one(number)",
                        "    x0 = add_one(x1)",
                        "    return add_one(x0)",
                    ]
                ),
            ]
        )

    def test_bfs_ordering(self):
        def add_one(number: int) -> int:
            return number + 1

        def double(number: int) -> int:
            return 2 * number

        self.fixture.given_program_inputs({"number": int})
        self.fixture.given_program_operations([add_one, double])
        self.fixture.given_output_type(int)
        self.fixture.given_agent(TopDownBFS())

        self.fixture.when_enumerating_generation(max_depth=2)
        self.fixture.then_generated_functions_asts_should_be(
            [
                # depth 0
                function_ast_from_source_lines(
                    [
                        "def generated_func(number: int):",
                        "    return number",
                    ]
                ),
                # depth 1
                function_ast_from_source_lines(
                    [
                        "def add_one(number: int) -> int:",
                        "   return number + 1",
                        "",
                        "def generated_func(number: int):",
                        "    return add_one(number)",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        "def double(number: int) -> int:",
                        "   return 2 * number",
                        "",
                        "def generated_func(number: int):",
                        "    return double(number)",
                    ]
                ),
                # depth 2
                function_ast_from_source_lines(
                    [
                        "def add_one(number: int) -> int:",
                        "   return number + 1",
                        "",
                        "def generated_func(number: int):",
                        "    x0 = add_one(number)",
                        "    return add_one(x0)",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        "def add_one(number: int) -> int:",
                        "   return number + 1",
                        "",
                        "def double(number: int) -> int:",
                        "   return 2 * number",
                        "",
                        "def generated_func(number: int):",
                        "    x0 = double(number)",
                        "    return add_one(x0)",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        "def add_one(number: int) -> int:",
                        "   return number + 1",
                        "",
                        "def double(number: int) -> int:",
                        "   return 2 * number",
                        "",
                        "def generated_func(number: int):",
                        "    x0 = add_one(number)",
                        "    return double(x0)",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        "def double(number: int) -> int:",
                        "   return 2 * number",
                        "",
                        "def generated_func(number: int):",
                        "    x0 = double(number)",
                        "    return double(x0)",
                    ]
                ),
            ]
        )


@pytest.fixture
def generation_fixture() -> "CodeGenerationFixture":
    return CodeGenerationFixture()


class CodeGenerationFixture:
    def __init__(self) -> None:
        self.generated_asts: list[ast.Module] = []
        self.inputs: dict[str, Type[Any]] = {}
        self.constants: dict[str, Any] = {}
        self.operations: list[Callable[..., Any]] = []
        self.agent: SynthesisAgent = TopDownBFS()
        self.std_operations: list[StandardOperation] = []

    def given_output_type(self, output_type: Type[object]) -> None:
        self.output_type = output_type

    def given_program_inputs(self, inputs: dict[str, Type[Any]]) -> None:
        self.inputs = inputs

    def given_program_constants(self, constants: dict[str, Any]) -> None:
        self.constants = constants

    def given_program_operations(self, operations: list[Callable[..., Any]]) -> None:
        self.operations = operations

    def given_program_standard_operations(
        self, standard_operations: list[StandardOperation]
    ) -> None:
        self.std_operations = standard_operations

    def given_agent(self, agent: SynthesisAgent) -> None:
        self.agent = agent

    def when_enumerating_generation(self, **kwargs):
        dsl = DomainSpecificLanguage(
            inputs=Input.from_dict(self.inputs),
            constants=Constant.from_dict(self.constants),
            operations=[Operation.from_func(op) for op in self.operations],
        )
        generator = ProgramGenerator(
            dsl=dsl,
            standard_operations=self.std_operations,
            output_type=self.output_type,
            agent=self.agent,
        )
        for program_graph in generator.enumerate(**kwargs):
            generated_program = graph_to_program(program_graph, "generated_func", dsl)
            self.generated_asts.append(ast.parse(generated_program.source))

    def then_generated_functions_asts_should_be(
        self, expected_asts: list[ast.Module]
    ) -> None:
        generated = to_source_list(self.generated_asts)
        expected = to_source_list(expected_asts)
        assert generated == expected, "\n".join(
            Differ().compare(
                json.dumps("\n".join(expected).splitlines(), indent=2).splitlines(),
                json.dumps("\n".join(generated).splitlines(), indent=2).splitlines(),
            )
        )
