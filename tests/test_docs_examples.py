from pathlib import Path


EXPECTED_SMALLEST_PROGRAM = """THREE = 3


def repeat(string: str, times: int) ->str:
    return string * times


def generated_func(input_string: str):
    return repeat(input_string, THREE)
"""


def test_readme_quickstart_example(tmp_path: Path) -> None:
    dsl_path = tmp_path / "example_dsl.py"
    dsl_path.write_text(
        "\n".join(
            (
                "# Define a small DSL",
                "",
                "## Constants",
                "",
                "TWO = 2",
                "THREE = 3",
                "",
                "",
                "## Operations",
                "",
                "def repeat(string: str, times: int) -> str:",
                "    return string * times",
                "",
                "",
                "def concat(string: str, other_string: str) -> str:",
                "    return string + other_string",
                "",
            )
        )
    )

    ### Example code begin

    from astsynth.synthesizer import Synthesizer
    from astsynth.task import Task
    from astsynth.dsl import load_symbols_from_python_file

    # Initialize the dsl
    dsl = load_symbols_from_python_file(dsl_path)

    # Make a task from a few i/o examples
    task = Task.from_tuples(
        [
            ({"input_string": "abc"}, "abcabcabc"),
            ({"input_string": "ab"}, "ababab"),
            ({"input_string": "abcd"}, "abcdabcdabcd"),
        ]
    )
    # Augment the dsl with task inputs
    dsl.add_task_inputs(task)

    # Synthesize all programs that succeeds at the task:
    synthesizer = Synthesizer(dsl=dsl, task=task)
    synthesis_result = synthesizer.run(max_depth=2)
    print(
        f"Found {synthesis_result.stats.n_successful_programs} successful programs"
        f" over the {synthesis_result.stats.n_generated_programs} generated"
        f" in {synthesis_result.stats.runtime:.2E}s",
    )

    # Write down the smallest solution program
    smallest_program = min(synthesis_result.successful_programs, key=lambda p: len(p))
    print(f"\nSmallest program found:\n\n{smallest_program.source}")

    print("Other successful programs found:")
    for program in synthesis_result.successful_programs:
        if program is smallest_program:
            continue
        print("-" * 30)
        print(f"\n{program.source}")

    assert smallest_program.source == EXPECTED_SMALLEST_PROGRAM
