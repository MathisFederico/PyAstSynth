import ast
from typing import Any, Generator, Optional, Type


class CodeGenerator:
    def __init__(
        self,
        allowed_constants: Optional[dict[str, Any]] = None,
        output_type: Type[object] = object,
    ) -> None:
        if allowed_constants is None:
            allowed_constants = {}
        self.allowed_constants = allowed_constants
        self.output_type = output_type

    def enumerate(self) -> Generator[ast.FunctionDef, None, None]:
        for constant_name, const in self.allowed_constants.items():
            if not isinstance(const, self.output_type):
                continue
            yield ast.FunctionDef(
                name=f"const_{const}",
                body=[ast.Return(ast.Name(constant_name))],
                decorator_list=[],
                args=ast.arguments(args=[], defaults=[]),
            )
