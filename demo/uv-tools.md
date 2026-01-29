
# Using tools in UV (uvx)

The command `uvx` is shorthand for running `uv tool run`

```bash
# Run ruff on folder
uvx ruff check . --fix

# Install pytest as a tool
uv tool install pytest
uvx pytest . # run it
```

## Install custom tool

```bash
# as simple as
uv tool install git+https://github.com/bjss/ai-code-combiner

# Then run it
uvx ai_code_combiner ai-specialist-template/ui/app.py
```
