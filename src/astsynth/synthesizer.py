from typing import TYPE_CHECKING, Optional

from astsynth.agent import SynthesisAgent, TopDownBFS
from astsynth.generator import ProgramGenerator
from astsynth.namer import DefaultProgramNamer, ProgramNamer
from astsynth.program import GeneratedProgram
from astsynth.program.validate import validate_program_on_task
from astsynth.program.writter import graph_to_program


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

    def find_valid_programs(
        self,
        max_depth: int = 3,
        namer: ProgramNamer = DefaultProgramNamer(),
    ) -> list[GeneratedProgram]:
        generator = ProgramGenerator(
            dsl=self.dsl, output_type=self.task.output_type, agent=self.brancher
        )

        valid_programs: list[GeneratedProgram] = []
        for program_graph in generator.enumerate(max_depth=max_depth):
            program_name = namer.name(program_graph)
            generated_program = graph_to_program(program_graph, program_name, self.dsl)
            validation_result = validate_program_on_task(generated_program, self.task)
            if validation_result.full_success:
                valid_programs.append(generated_program)

        return valid_programs
