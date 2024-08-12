import ast
from astsynth.program import GeneratedProgram
from astsynth.task import Example, Task


from pydantic import BaseModel


from typing import Any


class ExampleResult(BaseModel):
    example: Example
    result: Any

    @property
    def success(self) -> bool:
        return self.result == self.example.output


class ValidationResult(BaseModel):
    individual_results: list[ExampleResult]

    @property
    def full_success(self) -> bool:
        return all(res.success for res in self.individual_results)


def validate_program_on_task(
    program: "GeneratedProgram", task: "Task"
) -> ValidationResult:
    exec(compile(ast.parse(program.source), filename="<ast>", mode="exec"), locals())
    results = []
    for example in task.examples.values():
        call_result = eval(f"{program.name}(**example.input)")
        results.append(ExampleResult(example=example, result=call_result))
    return ValidationResult(individual_results=results)
