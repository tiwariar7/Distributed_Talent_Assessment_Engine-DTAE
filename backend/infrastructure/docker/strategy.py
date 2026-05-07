"""
Pluggable execution strategy pattern for different programming languages.

Provides compilation, runtime execution configuration, and resource tuning.
"""

from abc import ABC, abstractmethod
import shlex

class LanguageRunner(ABC):
    """Abstract base class for all language runtimes."""

    @property
    @abstractmethod
    def language(self) -> str:
        """The language identifier."""
        pass

    @abstractmethod
    def get_compile_command(self, source_file: str, output_dir: str) -> list[str] | None:
        """Returns the command list to compile the source file, or None."""
        pass

    @abstractmethod
    def get_execute_command(self, source_file: str, output_dir: str) -> list[str]:
        """Returns the command list to execute the compiled/interpreted program."""
        pass

    @abstractmethod
    def get_source_filename(self) -> str:
        """Returns the file name used for saving the source code."""
        pass

    @abstractmethod
    def sandbox_image(self) -> str:
        """The sandbox image containing the runner runtime environment."""
        pass

    def get_timeout_multiplier(self) -> float:
        """Language-specific timeout multiplier (e.g. JVM startup overhead)."""
        return 1.0

    def normalize_outputs(self, stdout: str, stderr: str) -> tuple[str, str]:
        """Strips leading/trailing whitespaces and cleans up standard streams."""
        return stdout.strip(), stderr.strip()

    def get_resource_limits(self) -> dict:
        """Language-specific Docker container resource limit overrides."""
        return {}


class PythonRunner(LanguageRunner):
    """Python 3 runtime execution strategy."""

    @property
    def language(self) -> str:
        return "python"

    def get_compile_command(self, source_file: str, output_dir: str) -> list[str] | None:
        return None

    def get_execute_command(self, source_file: str, output_dir: str) -> list[str]:
        return ["python3", source_file]

    def get_source_filename(self) -> str:
        return "solution.py"

    def sandbox_image(self) -> str:
        return "dtae/multi-sandbox:latest"


class JavaScriptRunner(LanguageRunner):
    """Node.js runtime execution strategy."""

    @property
    def language(self) -> str:
        return "javascript"

    def get_compile_command(self, source_file: str, output_dir: str) -> list[str] | None:
        return None

    def get_execute_command(self, source_file: str, output_dir: str) -> list[str]:
        return ["node", source_file]

    def get_source_filename(self) -> str:
        return "solution.js"

    def sandbox_image(self) -> str:
        return "dtae/multi-sandbox:latest"


class CppRunner(LanguageRunner):
    """G++ C++20 runtime execution strategy."""

    @property
    def language(self) -> str:
        return "cpp"

    def get_compile_command(self, source_file: str, output_dir: str) -> list[str] | None:
        return ["g++", "-O3", "-std=c++20", source_file, "-o", f"{output_dir}/solution"]

    def get_execute_command(self, source_file: str, output_dir: str) -> list[str]:
        return [f"{output_dir}/solution"]

    def get_source_filename(self) -> str:
        return "solution.cpp"

    def sandbox_image(self) -> str:
        return "dtae/multi-sandbox:latest"


class JavaRunner(LanguageRunner):
    """OpenJDK 21 runtime execution strategy."""

    @property
    def language(self) -> str:
        return "java"

    def get_compile_command(self, source_file: str, output_dir: str) -> list[str] | None:
        return ["javac", "-d", output_dir, source_file]

    def get_execute_command(self, source_file: str, output_dir: str) -> list[str]:
        return ["java", "-cp", output_dir, "Solution"]

    def get_source_filename(self) -> str:
        return "Solution.java"

    def sandbox_image(self) -> str:
        return "dtae/multi-sandbox:latest"

    def get_timeout_multiplier(self) -> float:
        return 1.5


RUNNERS: dict[str, LanguageRunner] = {
    "python": PythonRunner(),
    "javascript": JavaScriptRunner(),
    "cpp": CppRunner(),
    "java": JavaRunner(),
}


def get_runner(language: str) -> LanguageRunner:
    """Resolve the LanguageRunner strategy for a given language string."""
    runner = RUNNERS.get(language.lower())
    if not runner:
        raise ValueError(f"Unsupported execution language strategy: {language}")
    return runner

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Refactor variable names for better readability.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Refactor variable names for better readability.

# Refactor: Refactor variable names for better readability.

# Refactor: Update validation checks and constraints.
