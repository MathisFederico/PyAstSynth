from typing import Any, Generic, Self, Type, TypeVar
from pydantic import BaseModel


Input = TypeVar("Input")
Output = TypeVar("Output")


class Example(BaseModel):
    input: Any
    output: Any


class Task(BaseModel, Generic[Input, Output]):
    examples: dict[tuple[tuple[str, Input], ...], Example]
    input_types: dict[str, Type[Input]]
    output_type: Type[Output]

    @classmethod
    def from_tuples(cls, examples: list[tuple[dict[str, Input], Output]]) -> Self:
        defining_example = examples.pop()
        inputs_kwargs, output = defining_example
        input_types = {name: type(value) for name, value in inputs_kwargs.items()}
        output_type = type(output)

        formated_examples: dict[tuple[tuple[str, Input], ...], Example] = {}

        for inputs_kwargs, output in examples:
            for name, value in inputs_kwargs.items():
                if name not in input_types:
                    raise ValueError(
                        f"Unknown argument {name},"
                        f" not present in the defining example : {defining_example}"
                    )
                if not isinstance(value, input_types[name]):
                    raise TypeError(
                        f"Argument {name} is of type {type(value)},"
                        f" which is not compatible with types in the defining example : {defining_example}"
                    )
            if not isinstance(output, output_type):
                raise TypeError(
                    f"Output type {type(output)},"
                    f" is not compatible with output type of the defining example : {defining_example}"
                )
            input_hash = tuple([(name, value) for name, value in inputs_kwargs.items()])
            if input_hash in formated_examples:
                raise ValueError(
                    f"Input {inputs_kwargs} is already given in example {formated_examples[input_hash]} "
                )
            formated_examples[input_hash] = Example(input=inputs_kwargs, output=output)

        return cls(
            examples=formated_examples, input_types=input_types, output_type=output_type
        )
