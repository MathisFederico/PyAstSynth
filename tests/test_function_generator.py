import ast
import astor
import pytest

from astsynth.generator import ProgramGenerator


class TestGeneration:
    @pytest.fixture(autouse=True)
    def setup(self, generation_fixture: "CodeGenerationFixture"):
        self.fixture = generation_fixture

    def test_return_variable(self):
        """should be able to simply return variables (of the expected type) whether variables are constants or inputs."""
        self.fixture.given_code_generator(
            ProgramGenerator(
                inputs={"number": int, "desc": str},
                allowed_constants={"N": 42, "A": "a constant string"},
                output_type=int,
            )
        )
        self.fixture.when_enumerating_generation()
        self.fixture.then_generated_functions_asts_should_be(
            [
                function_ast_from_source_lines(
                    [
                        'A = "a constant string"',
                        "N = 42",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return number",
                    ]
                ),
                function_ast_from_source_lines(
                    [
                        'A = "a constant string"',
                        "N = 42",
                        "",
                        "def generated_func(number: int, desc: str):",
                        "    return N",
                    ]
                ),
            ]
        )

    def test_functions_usage(self):
        def concat_strings(string: str, other_string: str) -> str:
            return string + other_string

        def repeat(string: str, times: int) -> str:
            return string * times

        self.fixture.given_code_generator(
            ProgramGenerator(
                inputs={"number": int, "desc": str},
                allowed_constants={"N": 3, "A": "a"},
                operations=[concat_strings, repeat],
                output_type=str,
            )
        )
        self.fixture.when_enumerating_generation()

        common_code = [
            'A = "a"',
            "N = 42",
            "",
            "def generated_func(number: int, desc: str):",
        ]

        self.fixture.then_generated_functions_asts_should_be(
            [
                function_ast_from_source_lines(common_code + ["    return desc"]),
                function_ast_from_source_lines(common_code + ["    return A"]),
                function_ast_from_source_lines(
                    common_code + ["    return concat_strings(desc, desc)"]
                ),
                function_ast_from_source_lines(
                    common_code + ["    return concat_strings(desc, A)"]
                ),
                function_ast_from_source_lines(
                    common_code + ["    return concat_strings(A, desc)"]
                ),
                function_ast_from_source_lines(
                    common_code + ["    return concat_strings(A, A)"]
                ),
                function_ast_from_source_lines(
                    common_code + ["    return repeat(desc, number)"]
                ),
                function_ast_from_source_lines(
                    common_code + ["    return repeat(A, number)"]
                ),
            ]
        )


def function_ast_from_source_lines(source_lines: list[str]) -> ast.Module:
    return ast.parse("\n".join(source_lines))


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
