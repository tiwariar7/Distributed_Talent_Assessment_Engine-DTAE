import pytest
from infrastructure.docker.strategy import (
    get_runner,
    PythonRunner,
    JavaScriptRunner,
    CppRunner,
    JavaRunner,
)

def test_get_runner():
    """Verify that the correct runner instance is returned for each language choice."""
    assert isinstance(get_runner("python"), PythonRunner)
    assert isinstance(get_runner("javascript"), JavaScriptRunner)
    assert isinstance(get_runner("cpp"), CppRunner)
    assert isinstance(get_runner("java"), JavaRunner)

    with pytest.raises(ValueError):
        get_runner("unsupported-lang")

def test_python_runner():
    """Verify Python-specific strategy functions."""
    runner = get_runner("python")
    assert runner.get_source_filename() == "solution.py"
    assert runner.get_timeout_multiplier() == 1.0
    assert runner.get_compile_command("solution.py", "/tmp") is None
    
    exec_cmd = runner.get_execute_command("solution.py", "/tmp")
    assert exec_cmd == ["python3", "solution.py"]

    # Output normalization should strip trailing spaces/lines
    out, err = runner.normalize_outputs(" hello \n", " error \n")
    assert out == "hello"
    assert err == "error"

def test_javascript_runner():
    """Verify JavaScript-specific strategy functions."""
    runner = get_runner("javascript")
    assert runner.get_source_filename() == "solution.js"
    assert runner.get_timeout_multiplier() == 1.0
    assert runner.get_compile_command("solution.js", "/tmp") is None
    
    exec_cmd = runner.get_execute_command("solution.js", "/tmp")
    assert exec_cmd == ["node", "solution.js"]

def test_cpp_runner():
    """Verify C++-specific strategy functions with compilation."""
    runner = get_runner("cpp")
    assert runner.get_source_filename() == "solution.cpp"
    assert runner.get_timeout_multiplier() == 1.0
    
    compile_cmd = runner.get_compile_command("/tmp/solution.cpp", "/tmp")
    assert compile_cmd == ["g++", "-O3", "-std=c++20", "/tmp/solution.cpp", "-o", "/tmp/solution"]

    exec_cmd = runner.get_execute_command("/tmp/solution.cpp", "/tmp")
    assert exec_cmd == ["/tmp/solution"]

def test_java_runner():
    """Verify Java-specific strategy functions with compilation."""
    runner = get_runner("java")
    assert runner.get_source_filename() == "Solution.java"
    assert runner.get_timeout_multiplier() == 1.5
    
    compile_cmd = runner.get_compile_command("/tmp/Solution.java", "/tmp")
    assert compile_cmd == ["javac", "-d", "/tmp", "/tmp/Solution.java"]

    exec_cmd = runner.get_execute_command("/tmp/Solution.java", "/tmp")
    assert exec_cmd == ["java", "-cp", "/tmp", "Solution"]

# Refactor: Update validation checks and constraints.
