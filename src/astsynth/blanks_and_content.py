from dataclasses import dataclass, field
from enum import Enum
import inspect
from typing import Any, Callable, Optional, Type, Union
from typing_extensions import Self


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
    type: Type[Any] = field(repr=False)
    kind: VariableKind
    value: Optional[Any] = field(default=None, repr=False)

    def __hash__(self) -> int:
        return hash("Variable|" + self.name)


class AnnotationMissing(Exception):
    pass


@dataclass
class Operation:
    name: str
    func: Callable[..., Any] = field(repr=False)
    output_type: Type[Any] = field(repr=False)
    inputs_types: dict[str, Type[Any]] = field(repr=False)

    def __post_init__(self):
        self.arity: int = len(self.inputs_types)

    def __hash__(self) -> int:
        return hash("Operation|" + self.name)

    @classmethod
    def from_func(cls, func: Callable[..., Any]) -> Self:
        argspec = inspect.getfullargspec(func)
        for spec_name in argspec.args + ["return"]:
            if spec_name not in argspec.annotations:
                raise AnnotationMissing(
                    f"Annotation missing for {spec_name} of function {func.__name__} {repr(func)}",
                )
        output_type = argspec.annotations["return"]
        input_types = {
            arg_name: argspec.annotations[arg_name] for arg_name in argspec.args
        }
        return cls(
            name=func.__name__,
            func=func,
            output_type=output_type,
            inputs_types=input_types,
        )


BlankContent = Union[Variable, Operation]
