from pathlib import Path


def test_readme_quickstart_example(tmp_path: Path) -> None:
    dsl_path = tmp_path / "dsl.py"
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
    print(dsl)

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

    # Show inputs and expected output_type from the task
    print(task)

    # Synthesize all valid programs:
    synthesizer = Synthesizer(dsl=dsl, task=task)
    valid_programs = synthesizer.find_valid_programs(max_depth=3)
    print(f"Found {len(valid_programs)}")
    # assert len(valid_programs) == 2

    # Write down the smallest solution program
    smallest_program = min(valid_programs, key=lambda p: len(p))
    print(smallest_program.source)
    assert smallest_program.source == "\n".join(
        [
            "THREE = 3",
            "",
            "",
            "def repeat(string: str, times: int) ->str:",
            "    return string * times",
            "",
            "",
            "def generated_func(input_string: str):",
            "    return repeat(input_string, THREE)",
            "",
        ]
    )
