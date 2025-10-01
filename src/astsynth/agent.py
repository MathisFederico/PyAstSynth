from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Union

from pydantic import BaseModel, ConfigDict

from astsynth.program.blanks import (
    Blank,
    BlankContent,
    Constant,
    Input,
    ProgramHash,
)

if TYPE_CHECKING:
    from astsynth.program.graph import ProgramGraph


class Stop(BaseModel):
    model_config = ConfigDict(frozen=True)


class FillBlanks(BaseModel):
    model_config = ConfigDict(frozen=True)
    blanks_contents: tuple[tuple[Blank, BlankContent], ...]


class EmptySubBlanks(BaseModel):
    model_config = ConfigDict(frozen=True)
    parent_blank: Optional[Blank] = None
    blanks: tuple[Blank, ...]


class JumpToFrontiere(BaseModel):
    model_config = ConfigDict(frozen=True)
    config: ProgramHash


SynthAction = Union[Stop, FillBlanks, EmptySubBlanks, JumpToFrontiere]


class SynthesisAgent(ABC):
    """Agent choosing which program blank to fill and with what available content."""

    @abstractmethod
    def act(self, candidates: list[SynthAction], graph: "ProgramGraph") -> SynthAction:
        """Agent action in the given context."""


class TopDownBFS(SynthesisAgent):
    """Top down enumeration of all programs

    Simply fill all empty blanks then replace them with the first available option,
    priorizing options of same depth.

    """

    def __init__(self) -> None:
        self.blanks_with_other_constants: set[tuple[Blank, ...]] = set()

    def act(self, candidates: list[SynthAction], graph: "ProgramGraph") -> SynthAction:
        fill_blanks = [
            action for action in candidates if isinstance(action, FillBlanks)
        ]

        fill_blanks_with_variable: list[FillBlanks] = []
        for action in fill_blanks:
            if all_const(action):
                fill_blanks_with_variable.append(action)

        if fill_blanks_with_variable:
            fill_blank_action = fill_blanks_with_variable[0]
            current_blanks = set(
                blank for blank, _content in fill_blank_action.blanks_contents
            )

            other_blanks_constants: list[FillBlanks] = []
            for action in fill_blanks:
                other_blanks = set(blank for blank, _content in action.blanks_contents)
                if (
                    action != fill_blank_action
                    and other_blanks == current_blanks
                    and all_const(action)
                ):
                    other_blanks_constants.append(action)

            if other_blanks_constants:
                blanks = tuple(
                    [blank for blank, _content in fill_blank_action.blanks_contents]
                )
                self.blanks_with_other_constants.add(blanks)
            return fill_blank_action

        empty_blanks = [
            action for action in candidates if isinstance(action, EmptySubBlanks)
        ]
        for empty_blank_action in empty_blanks:
            if empty_blank_action.blanks in self.blanks_with_other_constants:
                self.blanks_with_other_constants.remove(empty_blank_action.blanks)
                return empty_blank_action

        available_frontiere = [
            action for action in candidates if isinstance(action, JumpToFrontiere)
        ]
        if available_frontiere:
            self.blanks_with_other_constants = set()
            return available_frontiere[0]

        empty_blanks = [
            action for action in candidates if isinstance(action, EmptySubBlanks)
        ]
        if empty_blanks:
            return empty_blanks[0]

        stop = [action for action in candidates if isinstance(action, Stop)].pop()
        return stop


def all_const(action: FillBlanks) -> bool:
    return all(
        isinstance(content, (Input, Constant))
        for _blank, content in action.blanks_contents
    )
