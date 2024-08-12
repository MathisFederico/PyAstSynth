from typing import TYPE_CHECKING, Optional

from astsynth.agent import SynthesisAgent, TopDownBFS
from astsynth.generator import ProgramGenerator
from astsynth.program import GeneratedProgram
from astsynth.program.validate import validate_program_on_task


if TYPE_CHECKING:
    from astsynth.dsl import DomainSpecificLanguage
    from astsynth.task import Task


class Synthesizer:
    def __init__(
        self,
        dsl: "DomainSpecificLanguage",
        task: "Task",
        agent: Optional[SynthesisAgent] = None,
    ) -> None:
        self.dsl = dsl
        self.task = task
        self.brancher = agent if agent is not None else TopDownBFS()

    def find_valid_programs(self, max_depth: int = 10) -> list[GeneratedProgram]:
        generator = ProgramGenerator(
            dsl=self.dsl, output_type=self.task.output_type, agent=self.brancher
        )

        valid_programs: list[GeneratedProgram] = []
        for program in generator.enumerate(max_depth=max_depth):
            validation_result = validate_program_on_task(program, self.task)
            if validation_result.full_success:
                valid_programs.append(program)

        return valid_programs
