import ast
import astor
from typing import Any, Type
import pytest

from astsynth.generator import FunctionGenerator


def test_return_variable(generation_fixture: "CodeGenerationFixture"):
    """should be able to simply return variables (of the expected type) whether variables are constants or inputs."""
    generation_fixture.given_inputs({"number": 2, "desc": "input_string"})
    generation_fixture.given_allowed_constants({"N": 42, "A": "a constant string"})
    generation_fixture.given_expected_output_type(int)
    generation_fixture.when_enumerating_generation()
    generation_fixture.then_generated_functions_asts_should_be(
        set(
            [
                function_ast_from_source(
                    "\n".join(
                        [
                            'A = "a constant string"',
                            "N = 42",
                            "",
                            "def const_n(number: int, desc: str):",
                            "    return N",
                        ]
                    )
                ),
                function_ast_from_source(
                    "\n".join(
                        [
                            'A = "a constant string"',
                            "N = 42",
                            "",
                            "def const_number(number: int, desc: str):",
                            "    return number",
                        ]
                    )
                ),
            ]
        )
    )


def function_ast_from_source(source: str) -> ast.Module:
    return ast.parse(source)


@pytest.fixture
def generation_fixture() -> "CodeGenerationFixture":
    return CodeGenerationFixture()


class CodeGenerationFixture:
    def __init__(self) -> None:
        self.code_generator = FunctionGenerator()
        self.generated_codes: list[str] = []

    def given_inputs(self, inputs: dict[str, Any]):
        self.code_generator.inputs = inputs

    def given_allowed_constants(self, constants: dict[str, Any]):
        self.code_generator.allowed_constants = constants

    def given_expected_output_type(self, expected_output_type: Type[object]):
        self.code_generator.output_type = expected_output_type

    def when_enumerating_generation(self):
        for program_tree in self.code_generator.enumerate():
            self.generated_codes.append(program_tree)

    def then_generated_functions_asts_should_be(self, expected_functions: set[str]):
        assert set(astor.to_source(tree) for tree in self.generated_codes) == set(
            astor.to_source(tree) for tree in expected_functions
        )
