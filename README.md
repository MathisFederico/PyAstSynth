# PyAstSynth : A library from python program synthesis

## Installation

```bash
pip install git+https://github.com/MathisFederico/PyAstSynth
```

## Usage

First define a Domain specific language for your application.
It can be a simple list of python functions like this:

```python
# --> example_dsl.py

# Define a small DSL

## Constants
TWO = 2
THREE = 3

## Operations

def repeat(string: str, times: int) -> str:
    return string * times


def concat(string: str, other_string: str) -> str:
    return string + other_string

```

Then use astsynth to find the all successful programs on the task and print the smallest:

```python
# --> main.py

from pathlib import Path
from astsynth.synthesizer import Synthesizer
from astsynth.task import Task
from astsynth.dsl import load_symbols_from_python_file

# Initialize the dsl
dsl_path = Path("./example_dsl.py")
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
    f"over the {synthesis_result.stats.n_generated_programs} generated programs",
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

```

This will print:

```bash
Found 5 successful programs over the 20 generated in 1.40E-01s

Smallest program found:

THREE = 3


def repeat(string: str, times: int) ->str:
    return string * times


def generated_func(input_string: str):
    return repeat(input_string, THREE)

Other successful programs found:
------------------------------

TWO = 2


def concat(string: str, other_string: str) ->str:
    return string + other_string


def repeat(string: str, times: int) ->str:
    return string * times


def generated_func(input_string: str):
    x0 = repeat(input_string, TWO)
    return concat(input_string, x0)

------------------------------

def concat(string: str, other_string: str) ->str:
    return string + other_string


def generated_func(input_string: str):
    x0 = concat(input_string, input_string)
    return concat(input_string, x0)

------------------------------

TWO = 2


def concat(string: str, other_string: str) ->str:
    return string + other_string


def repeat(string: str, times: int) ->str:
    return string * times


def generated_func(input_string: str):
    x0 = repeat(input_string, TWO)
    return concat(x0, input_string)

------------------------------

def concat(string: str, other_string: str) ->str:
    return string + other_string


def generated_func(input_string: str):
    x0 = concat(input_string, input_string)
    return concat(x0, input_string)

```

## Contributing

Fork this repository and clone the forked one:
```
git clone https://github.com/<Your Username>/PyAstSynth
```

Navigate to the local repository:
```bash
cd path/to/local/repo
```

Install in editable mode with dev requirements:
```bash
pip install -e .[dev]
```

Install pre-commit and pre-push hooks:
```bash
pre-commit install -t pre-commit -t pre-push
```

Run a pre-push check (that includes tests):
```bash
pre-commit run --hook-stage pre-push
```

Do your modifications and push them
```bash
git push
```

Ensure to have a test for each bugfix / feature you have done.

Then do a pull request from your fork to the original repository with the changes, mentionning issues you are solving or features you are adding.
