import time
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

from astsynth.agent import SynthesisAgent, TopDownBFS
from astsynth.generator import ProgramGenerator
from astsynth.namer import DefaultProgramNamer, ProgramNamer
from astsynth.program import GeneratedProgram
from astsynth.program.evaluate import evaluate_program_on_task
from astsynth.program.writter import graph_to_program


if TYPE_CHECKING:
    from astsynth.dsl import DomainSpecificLanguage
    from astsynth.task import Task


class SynthesisStatistics(BaseModel):
    """Statistics of the program synthesis."""

    n_generated_programs: int
    """Number of programs generated during the synthesis."""
    n_successful_programs: int
    """Number of programs generated that successfully gives the right output from the inputs on every example of the task."""
    runtime: float
    """The runtime (s) of the synthesis."""


class SynthesisResult(BaseModel):
    successful_programs: list[GeneratedProgram]
    """List of programs generated that successfully gives the right output from the inputs on every example of the task."""
    stats: SynthesisStatistics
    """Statistics of the synthesis process."""


class Synthesizer:
    def __init__(
        self,
        dsl: "DomainSpecificLanguage",
        task: "Task",
        agent: Optional[SynthesisAgent] = None,
    ) -> None:
        self.dsl = dsl
        self.task = task
        self.agent = agent if agent is not None else TopDownBFS()

    def run(
        self,
        max_depth: int = 3,
        namer: ProgramNamer = DefaultProgramNamer(),
    ) -> SynthesisResult:
        generator = ProgramGenerator(
            dsl=self.dsl, output_type=self.task.output_type, agent=self.agent
        )

        successful_programs: list[GeneratedProgram] = []
        n_generated = 0

        start_time = time.perf_counter()
        for program_graph in generator.enumerate(max_depth=max_depth):
            n_generated += 1
            program_name = namer.name(program_graph)
            generated_program = graph_to_program(program_graph, program_name, self.dsl)
            eval_result = evaluate_program_on_task(generated_program, self.task)
            if eval_result.full_success:
                successful_programs.append(generated_program)
        runtime = time.perf_counter() - start_time

        return SynthesisResult(
            successful_programs=successful_programs,
            stats=SynthesisStatistics(
                n_generated_programs=n_generated,
                n_successful_programs=len(successful_programs),
                runtime=runtime,
            ),
        )
