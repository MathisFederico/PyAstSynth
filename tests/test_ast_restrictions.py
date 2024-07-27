import ast
import astor
from typing import Any, Type
import pytest

from astsynth.generator import CodeGenerator


def test_return_constant(generation_fixture: "CodeGenerationFixture"):
    """should be limited to simple constant return if only constants are given."""
    generation_fixture.given_allowed_constants({"A": "a", "B": "b"})
    generation_fixture.when_enumerating_generation()
    generation_fixture.then_generated_functions_asts_should_be(
        set(
            [
                function_ast_from_source("def const_a():\n    return A"),
                function_ast_from_source("def const_b():\n    return B"),
            ]
        )
    )


def test_restrict_to_expected_type(generation_fixture: "CodeGenerationFixture"):
    generation_fixture.given_expected_output_type(int)
    generation_fixture.given_allowed_constants({"N": 42, "A": "a"})
    generation_fixture.when_enumerating_generation()
    generation_fixture.then_generated_functions_asts_should_be(
        set([function_ast_from_source("def const_42():\n    return N")])
    )


def function_ast_from_source(source: str):
    return ast.parse(source).body[0]


@pytest.fixture
def generation_fixture() -> "CodeGenerationFixture":
    return CodeGenerationFixture()


class CodeGenerationFixture:
    def __init__(self) -> None:
        self.code_generator = CodeGenerator()
        self.generated_codes: list[str] = []

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
