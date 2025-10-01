from typing import Type
from typing_extensions import Self
import pytest

from astsynth.program.blanks import Blank, BlankContent, Input, Operation
from astsynth.program.graph import ProgramGraph


class TestProgramGraph:
    @pytest.fixture(autouse=True)
    def setup(self, graph_fixture: "ProgramGraphFixture") -> None:
        self.fixture = graph_fixture

    def test_fill_blank_variable(self):
        """should fill an empty blank with a variable."""
        self.fixture.given_graph(ProgramGraphBuilder().build())

        variable = Input(name="x", type=str)
        return_blank = Blank(id="return", type=object)
        self.fixture.when_filling_blank(return_blank, variable)
        self.fixture.then_blank_value_should_be(return_blank, variable)
        self.fixture.then_empty_blanks_should_be(set())

    def test_replace_blank_variable(self):
        """should replace a filled blank with an other variable."""
        return_blank = Blank(id="return", type=object)
        initial_variable = Input(name="x", type=str)
        self.fixture.given_graph(
            ProgramGraphBuilder()
            .with_filled_blank(return_blank, initial_variable)
            .build()
        )

        new_content = Input(name="y", type=str)
        self.fixture.when_replacing_blank(return_blank, new_content)
        self.fixture.then_blank_value_should_be(return_blank, new_content)
        self.fixture.then_empty_blanks_should_be(set())

    def test_fill_blank_operation(self):
        """should fill an empty blank with an operation
        and create new empty blanks for its arguments."""
        self.fixture.given_graph(ProgramGraphBuilder().build())

        def add(x: int, y: int) -> int:
            return x + y

        operation = Operation.from_func(add)
        return_blank = Blank(id="return", type=object)
        self.fixture.when_filling_blank(return_blank, operation)
        self.fixture.then_blank_value_should_be(return_blank, operation)
        self.fixture.then_empty_blanks_should_be(
            {Blank(id="return>add>x", type=int), Blank(id="return>add>y", type=int)}
        )

    def test_replace_blank_operation(self):
        """should replace a filled blank with an operation
        and create new empty blanks for its arguments
        and deactivate replaced operation blanks."""
        return_blank = Blank(id="return", type=object)

        def sub(x: int, y: int) -> int:
            return x - y

        initial_operation = Operation.from_func(sub)
        self.fixture.given_graph(
            ProgramGraphBuilder()
            .with_filled_blank(return_blank, initial_operation)
            .build()
        )

        def add(x: int, y: int) -> int:
            return x + y

        new_operation = Operation.from_func(add)
        self.fixture.when_replacing_blank(return_blank, new_operation)
        self.fixture.then_blank_value_should_be(return_blank, new_operation)
        self.fixture.then_empty_blanks_should_be(
            {Blank(id="return>add>x", type=int), Blank(id="return>add>y", type=int)}
        )


@pytest.fixture
def graph_fixture() -> "ProgramGraphFixture":
    return ProgramGraphFixture()


class ProgramGraphFixture:
    def __init__(self) -> None:
        self.graph: ProgramGraph = ProgramGraph()

    def given_graph(self, graph: ProgramGraph) -> None:
        self.graph = graph

    def when_filling_blank(self, blank: Blank, content: BlankContent) -> None:
        self.graph.fill_blank(blank=blank, content=content)

    def when_replacing_blank(self, blank: Blank, content: BlankContent) -> None:
        self.graph.replace_blank(blank, content)

    def then_blank_value_should_be(
        self, blank: Blank, expected_content: BlankContent
    ) -> None:
        assert self.graph.content(blank) == expected_content

    def then_empty_blanks_should_be(self, expected_empty_blanks: set[Blank]) -> None:
        assert set(self.graph.empty_blanks) == expected_empty_blanks


class ProgramGraphBuilder:
    def __init__(self, output_type: Type[object] = object) -> None:
        self.graph = ProgramGraph(output_type=output_type)

    def with_filled_blank(self, blank: Blank, content: BlankContent) -> Self:
        self.graph.fill_blank(blank, content)
        return self

    def build(self) -> ProgramGraph:
        return self.graph
