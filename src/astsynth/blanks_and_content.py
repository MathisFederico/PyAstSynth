from dataclasses import dataclass
from enum import Enum
from typing import Any, Type


class VariableKind(Enum):
    INPUT = "input"
    CONSTANT = "constant"


@dataclass
class Variable:
    name: str
    value: Any
    kind: VariableKind

    def __post_init__(self):
        self.type = type(self.value)

    def __hash__(self) -> int:
        return hash("Variable|" + self.name)


@dataclass
class Blank:
    id: str
    type: Type[object]

    def __str__(self) -> str:
        return "□"

    def __hash__(self) -> int:
        return hash("Blank|" + self.id)
