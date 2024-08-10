from typing import Any, Callable, Generic, Type, TypeVar, Union
from typing_extensions import Self
import inspect

from pydantic import BaseModel


class Blank(BaseModel):
    id: str
    type: Type[object]

    def __str__(self) -> str:
        return "□"

    def __hash__(self) -> int:
        return hash("Blank|" + self.id)


class Input(BaseModel):
    name: str
    type: Type[Any]

    def __hash__(self) -> int:
        return hash("Input|" + self.name)

    @classmethod
    def from_dict(cls, variable_data: dict[str, Type[Any]]) -> list[Self]:
        return [cls(name=name, type=type) for name, type in variable_data.items()]


T = TypeVar("T")


class Constant(BaseModel, Generic[T]):
    name: str
    value: T

    @property
    def type(self) -> Type[T]:
        return type(self.value)

    def __hash__(self) -> int:
        return hash("Constant|" + self.name)

    @classmethod
    def from_dict(cls, variable_data: dict[str, Any]) -> list[Self]:
        return [cls(name=name, value=value) for name, value in variable_data.items()]


class AnnotationMissing(Exception):
    pass


class Operation(BaseModel):
    name: str
    source: str
    output_type: Type[Any]
    inputs_types: dict[str, Type[Any]]

    @property
    def arity(self) -> int:
        return len(self.inputs_types)

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

        source = function_source(func)
        return cls(
            name=func.__name__,
            source=source,
            output_type=output_type,
            inputs_types=input_types,
        )


Variable = Union[Input, Constant]
BlankContent = Union[Variable, Operation]


def function_source(func: Callable) -> str:
    lines = inspect.getsourcelines(func)[0]
    indent = 0
    for char in lines[0]:
        if char != " ":
            break
        indent += 1
    return "".join([line[indent:] for line in lines])
