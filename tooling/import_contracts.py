"""Execute Import Linter's real command entry point, including its exit status."""

from importlinter.cli import lint_imports_command

if __name__ == "__main__":
    lint_imports_command()
