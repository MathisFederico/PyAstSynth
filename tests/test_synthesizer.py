from typing import Any

import pytest


from astsynth.generator import GeneratedProgram
from astsynth.synthesizer import Synthesizer
from tests.conftest import function_ast_from_source_lines


class TestSynthesizer:
    @pytest.fixture(autouse=True)
    def setup(self, synthesizer_fixture: "SynthesizerFixture") -> None:
        self.fixture = synthesizer_fixture

    def test_simple_io_validating(self):
        self.fixture.given_generated_programs(
            [
                GeneratedProgram(
                    name="prog_2",
                    ast=function_ast_from_source_lines(
                        [
                            "TWO = 2",
                            "",
                            "def prog_2(number: int):",
                            "    return TWO",
                        ]
                    ),
                ),
                GeneratedProgram(
                    name="prog_2p3",
                    ast=function_ast_from_source_lines(
                        [
                            "TWO = 2",
                            "THREE = 3",
                            "",
                            "def add(x:int, y:int):",
                            "    return x + y",
                            "",
                            "def prog_2p3(number: int):",
                            "    return add(TWO, THREE)",
                        ]
                    ),
                ),
                GeneratedProgram(
                    name="prog_3txp2",
                    ast=function_ast_from_source_lines(
                        [
                            "TWO = 2",
                            "THREE = 3",
                            "",
                            "def add(x:int, y:int):",
                            "    return x + y",
                            "",
                            "def mul(x:int, y:int):",
                            "    return x * y",
                            "",
                            "def prog_3txp2(number: int):",
                            "    x0 = mul(number, THREE)",
                            "    return add(x0, TWO)",
                        ]
                    ),
                ),
                GeneratedProgram(
                    name="prog_xpxpxp2",
                    ast=function_ast_from_source_lines(
                        [
                            "TWO = 2",
                            "",
                            "def add(x:int, y:int):",
                            "    return x + y",
                            "",
                            "def prog_xpxpxp2(number: int):",
                            "    x1 = add(number, number)",
                            "    x0 = add(x1, number)",
                            "    return add(x0, TWO)",
                        ]
                    ),
                ),
            ]
        )
        self.fixture.given_IO_examples([(0, 2), (1, 5), (2, 8), (3, 11)])
        self.fixture.when_validating_generated_programs(max_depth=3)
        self.fixture.then_valid_programs_names_should_be(["prog_3txp2", "prog_xpxpxp2"])


@pytest.fixture
def synthesizer_fixture() -> "SynthesizerFixture":
    return SynthesizerFixture()


class SynthesizerFixture:
    def __init__(self) -> None:
        self.synthesizer = Synthesizer()
        self.valid_programs: list[GeneratedProgram] = []
        self.generated_programs: list[GeneratedProgram] = []

    def given_generated_programs(
        self, generated_programs: list[GeneratedProgram]
    ) -> None:
        self.generated_programs = generated_programs

    def given_IO_examples(self, io_examples: list[tuple[Any, Any]]) -> None:
        for input, output in io_examples:
            self.synthesizer.add_example(input=input, output=output)

    def when_validating_generated_programs(self, **kwargs: Any) -> None:
        self.valid_programs = [
            program
            for program in self.generated_programs
            if self.synthesizer.validate_program(program=program).full_success
        ]

    def then_valid_programs_names_should_be(self, expected_programs: list[str]) -> None:
        valid_names = [p.name for p in self.valid_programs]
        assert valid_names == expected_programs
