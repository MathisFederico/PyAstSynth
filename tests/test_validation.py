from typing import Any, Optional

import pytest


from astsynth.program import GeneratedProgram
from astsynth.task import Task
from astsynth.program.validate import validate_program_on_task


class TestSynthesizer:
    @pytest.fixture(autouse=True)
    def setup(self, validation_fixture: "ValidationFixture") -> None:
        self.fixture = validation_fixture

    def test_simple_io_validating(self):
        self.fixture.given_generated_programs(
            [
                GeneratedProgram(
                    name="prog_2",
                    source="\n".join(
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
                    source="\n".join(
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
                    source="\n".join(
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
                    source="\n".join(
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
        self.fixture.given_IO_examples(
            [
                ({"number": 0}, 2),
                ({"number": 1}, 5),
                ({"number": 2}, 8),
                ({"number": 3}, 11),
            ]
        )
        self.fixture.when_validating_generated_programs(max_depth=3)
        self.fixture.then_valid_programs_names_should_be(["prog_3txp2", "prog_xpxpxp2"])


@pytest.fixture
def validation_fixture() -> "ValidationFixture":
    return ValidationFixture()


class ValidationFixture:
    def __init__(self) -> None:
        self.valid_programs: list[GeneratedProgram] = []
        self.generated_programs: list[GeneratedProgram] = []
        self.task: Optional[Task] = None

    def given_generated_programs(
        self, generated_programs: list[GeneratedProgram]
    ) -> None:
        self.generated_programs = generated_programs

    def given_IO_examples(self, io_examples: list[tuple[dict[str, Any], Any]]) -> None:
        self.task = Task.from_tuples(io_examples)

    def when_validating_generated_programs(self, **kwargs: Any) -> None:
        if self.task is None:
            raise TypeError("Task must be defined first")
        self.valid_programs = [
            program
            for program in self.generated_programs
            if validate_program_on_task(program=program, task=self.task).full_success
        ]

    def then_valid_programs_names_should_be(self, expected_programs: list[str]) -> None:
        valid_names = [p.name for p in self.valid_programs]
        assert valid_names == expected_programs
