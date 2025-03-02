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

Then use astsynth to find the all valid programs and print the smallest:

```python
# --> main.py

from pathlib import Path
import time
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

# Synthesize all valid programs:
synthesizer = Synthesizer(dsl=dsl, task=task)
t0 = time.time()
valid_programs = synthesizer.find_valid_programs(max_depth=2)
time_taken = time.time() - t0
print(f"Found {len(valid_programs)} valid programs in {time_taken:.2E}s")

# Write down the smallest solution program
smallest_program = min(valid_programs, key=lambda p: len(p))
print(f"\nSmallest program found:\n\n{smallest_program.source}")
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
