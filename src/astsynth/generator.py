import ast
from typing import Any, Generator, Optional, Type


class FunctionGenerator:
    def __init__(
        self,
        inputs: Optional[dict[str, Any]] = None,
        allowed_constants: Optional[dict[str, Any]] = None,
        output_type: Type[object] = object,
    ) -> None:
        if allowed_constants is None:
            allowed_constants = {}
        self.allowed_constants = allowed_constants
        if inputs is None:
            inputs = {}
        self.inputs = inputs
        self.output_type = output_type

    def enumerate(self) -> Generator[ast.Module, None, None]:
        constants: list[ast.Assign] = []
        for constant_name, const in self.allowed_constants.items():
            constants.append(
                ast.Assign(targets=[ast.Name(constant_name)], value=ast.Constant(const))
            )
        constants.sort(key=lambda c: c.targets[0].id)

        variables = self.allowed_constants.copy()
        variables.update(self.inputs)

        return_candidates = [
            (constant_name, type(const)) for constant_name, const in variables.items()
        ]
        for candidate_name, canditate_type in return_candidates:
            if not issubclass(canditate_type, self.output_type):
                continue

            function = ast.FunctionDef(
                name=f"const_{candidate_name.lower()}",
                body=[ast.Return(ast.Name(candidate_name))],
                decorator_list=[],
                args=ast.arguments(
                    args=[
                        ast.arg(input_name, annotation=ast.Name(type(input).__name__))
                        for input_name, input in self.inputs.items()
                    ],
                    defaults=[],
                ),
            )

            yield ast.Module(body=constants + [function])
