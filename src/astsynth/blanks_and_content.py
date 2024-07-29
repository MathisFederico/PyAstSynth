from dataclasses import dataclass
from enum import Enum
import inspect
from typing import Any, Callable, Optional, Type


class VariableKind(Enum):
    INPUT = "input"
    CONSTANT = "constant"


@dataclass
class Blank:
    id: str
    type: Type[object]

    def __str__(self) -> str:
        return "□"

    def __hash__(self) -> int:
        return hash("Blank|" + self.id)


@dataclass
class Variable:
    name: str
    type: Type[Any]
    kind: VariableKind
    value: Optional[Any] = None

    def __hash__(self) -> int:
        return hash("Variable|" + self.name)


@dataclass
class Operation:
    name: str
    func: Callable[..., Any]
    output_type: Type[Any]
    inputs_types: list[Type[Any]]

    def __post_init__(self):
        self.arity: int = len(self.inputs_types)

    def __hash__(self) -> int:
        return hash("Operation|" + self.name)

    @classmethod
    def from_func(cls, func: Callable[..., Any]):
        argspec = inspect.getfullargspec(func)
        output_type = argspec.annotations["return"]
        input_types = [argspec.annotations[arg_name] for arg_name in argspec.args]
        return cls(
            name=func.__name__,
            func=func,
            output_type=output_type,
            inputs_types=input_types,
        )
