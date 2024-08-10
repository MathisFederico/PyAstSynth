import ast
from typing import Any, Callable, Type
import astor
import pytest

from astsynth.blanks_and_content import Input, Operation, Constant
from astsynth.dsl import DomainSpecificLanguage
from astsynth.generator import ProgramGenerator

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
        self.fixture.when_enumerating_generation()
        self.fixture.then_generated_functions_asts_should_be(
            [
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

    def test_operation_on_variables(self):
        def concat_strings(string: str, other_string: str) -> str:
            return string + other_string

        def repeat(string: str, times: int) -> str:
            return string * times

        self.fixture.given_program_inputs({"number": int, "desc": str})
        self.fixture.given_program_constants({"A": "a"})
        self.fixture.given_program_operations([concat_strings, repeat])
        self.fixture.given_output_type(str)

        self.fixture.when_enumerating_generation()
        self.fixture.then_generated_functions_asts_should_be(
            [
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
                        "    return concat_strings(A, A)",
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

        self.fixture.when_enumerating_generation(max_depth=3)
        self.fixture.then_generated_functions_asts_should_be(
            [
                function_ast_from_source_lines(
                    [
                        "def generated_func(number: int):",
                        "    return number",
                    ]
                ),
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
                        "def generated_func(number: int):",
                        "    x1 = add_one(number)",
                        "    x0 = add_one(x1)",
                        "    return add_one(x0)",
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

    def given_output_type(self, output_type: Type[object]) -> None:
        self.output_type = output_type

    def given_program_inputs(self, inputs: dict[str, Type[Any]]) -> None:
        self.inputs = inputs

    def given_program_constants(self, constants: dict[str, Any]) -> None:
        self.constants = constants

    def given_program_operations(self, operations: list[Callable[..., Any]]) -> None:
        self.operations = operations

    def when_enumerating_generation(self, **kwargs):
        dsl = DomainSpecificLanguage(
            inputs=Input.from_dict(self.inputs),
            constants=Constant.from_dict(self.constants),
            operations=[Operation.from_func(op) for op in self.operations],
        )
        generator = ProgramGenerator(dsl=dsl, output_type=self.output_type)
        for generated_program in generator.enumerate(**kwargs):
            astor.to_source(generated_program.ast)
            self.generated_asts.append(generated_program.ast)

    def then_generated_functions_asts_should_be(
        self, expected_asts: list[ast.Module]
    ) -> None:
        generated = to_source_list(self.generated_asts)
        expected = to_source_list(expected_asts)
        assert generated == expected
