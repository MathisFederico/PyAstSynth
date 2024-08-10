from dataclasses import dataclass
from typing import Any, Optional

from astsynth.generator import GeneratedProgram


@dataclass
class Example:
    input: Any
    output: Any


@dataclass
class ExampleResult:
    example: Example
    result: Any
    success: Optional[bool] = False

    def __post_init__(self):
        self.success: bool = self.result == self.example.output


@dataclass
class ValidationResult:
    individual_results: list[ExampleResult]
    full_success: Optional[bool] = False

    def __post_init__(self):
        self.full_success: bool = all(res.success for res in self.individual_results)


class Validator:
    def __init__(self) -> None:
        self.examples: dict[Any, Example] = {}

    def add_example(self, input: Any, output: Any) -> None:
        if input in self.examples:
            raise ValueError(
                f"An example was already given for input {input} resulting in {self.examples[input]}"
            )
        self.examples[input] = Example(input=input, output=output)

    def validate_program(self, program: GeneratedProgram) -> ValidationResult:
        exec(compile(program.ast, filename="<ast>", mode="exec"), locals())
        results = []
        for input, example in self.examples.items():
            results.append(
                ExampleResult(example=example, result=eval(f"{program.name}({input})"))
            )
        return ValidationResult(individual_results=results)
