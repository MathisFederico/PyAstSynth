from pathlib import Path
from typing import Any

import pytest

from astsynth.program.blanks import Operation, Constant
from astsynth.dsl import DomainSpecificLanguage, load_symbols_from_python_source


class TestDSL:
    @pytest.fixture(autouse=True)
    def setup(self, generation_fixture: "DSLFixture") -> None:
        self.fixture = generation_fixture

    def test_load_dsl_from_file(self, tmp_path: Path) -> None:
        dsl_source = "\n".join(
            (
                "# Define a small DSL",
                "",
                "## Constants",
                "",
                "TWO = 2",
                "THREE = 3",
                "",
                "## Operations",
                "",
                "",
                "def repeat(string: str, times: int) -> str:",
                "    return string * times",
                "",
                "",
                "def concat(string: str, other_string: str) -> str:",
                "    return string + other_string",
                "",
            )
        )

        def repeat(string: str, times: int) -> str:
            return string * times

        def concat(string: str, other_string: str) -> str:
            return string + other_string

        dsl_path = tmp_path / "dsl.py"
        self.fixture.given_python_file(at=dsl_path, content=dsl_source)
        self.fixture.when_loading_from_python_file(dsl_path)
        self.fixture.then_constants_should_be({"TWO": 2, "THREE": 3})
        self.fixture.then_operations_should_be(
            [Operation.from_func(repeat), Operation.from_func(concat)]
        )


@pytest.fixture
def generation_fixture() -> "DSLFixture":
    return DSLFixture()


class DSLFixture:
    def __init__(self) -> None:
        self.dsl = DomainSpecificLanguage()

    def given_python_file(self, at: Path, content: str) -> None:
        with open(at, mode="w") as pyfile:
            pyfile.write(content)

    def when_loading_from_python_file(self, file_path: Path) -> None:
        with open(file_path) as pyfile:
            py_src = pyfile.read()
        self.dsl.augment(load_symbols_from_python_source(py_src))

    def then_constants_should_be(self, expected_constants: dict[str, Any]) -> None:
        assert self.dsl.constants == Constant.from_dict(expected_constants)

    def then_operations_should_be(self, expected_ops: list[Operation]) -> None:
        assert self.dsl.operations == expected_ops
