import ast
import astor
import pytest

from astsynth.generator import ProgramGenerator

from tests.conftest import function_ast_from_source_lines, to_source_list


class TestGeneration:
    @pytest.fixture(autouse=True)
    def setup(self, generation_fixture: "CodeGenerationFixture") -> None:
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

        self.fixture.given_code_generator(
            ProgramGenerator(
                inputs={"number": int, "desc": str},
                allowed_constants={"A": "a"},
                operations=[concat_strings, repeat],
                output_type=str,
            )
        )
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

        self.fixture.given_code_generator(
            ProgramGenerator(
                inputs={"number": int},
                operations=[add_one],
                output_type=int,
            )
        )
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
        self.generator = ProgramGenerator()
        self.generated_asts: list[ast.Module] = []

    def given_code_generator(self, generator: ProgramGenerator) -> None:
        self.generator = generator

    def when_enumerating_generation(self, **kwargs):
        for generated_program in self.generator.enumerate(**kwargs):
            astor.to_source(generated_program.ast)
            self.generated_asts.append(generated_program.ast)

    def then_generated_functions_asts_should_be(
        self, expected_asts: list[ast.Module]
    ) -> None:
        generated = to_source_list(self.generated_asts)
        expected = to_source_list(expected_asts)
        assert generated == expected
