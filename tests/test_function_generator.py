import ast
import astor
import pytest

from astsynth.generator import ProgramGenerator


def test_return_variable(generation_fixture: "CodeGenerationFixture"):
    """should be able to simply return variables (of the expected type) whether variables are constants or inputs."""
    generation_fixture.given_code_generator(
        ProgramGenerator(
            inputs={"number": 2, "desc": "input_string"},
            allowed_constants={"N": 42, "A": "a constant string"},
            output_type=int,
        )
    )
    generation_fixture.when_enumerating_generation()
    generation_fixture.then_generated_functions_asts_should_be(
        [
            function_ast_from_source(
                "\n".join(
                    [
                        'A = "a constant string"',
                        "N = 42",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return number",
                    ]
                )
            ),
            function_ast_from_source(
                "\n".join(
                    [
                        'A = "a constant string"',
                        "N = 42",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return N",
                    ]
                )
            ),
        ]
    )


def function_ast_from_source(source: str) -> ast.Module:
    return ast.parse(source)


@pytest.fixture
def generation_fixture() -> "CodeGenerationFixture":
    return CodeGenerationFixture()


class CodeGenerationFixture:
    def __init__(self) -> None:
        self.generator = ProgramGenerator()
        self.generated_codes: list[str] = []

    def given_code_generator(self, generator: ProgramGenerator):
        self.generator = generator

    def when_enumerating_generation(self):
        for program_tree in self.generator.enumerate():
            self.generated_codes.append(program_tree)

    def then_generated_functions_asts_should_be(self, expected_functions: set[str]):
        assert _to_source_list(self.generated_codes) == _to_source_list(
            expected_functions
        )


def _to_source_list(asts: list[ast.Module]) -> list[str]:
    return [astor.to_source(tree) for tree in asts]
