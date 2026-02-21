"""
Secure, isolated code execution inside ephemeral Docker containers.

Each submission runs in a fresh container with memory and CPU limits.
The host never executes untrusted bytecode directly.
"""

from __future__ import annotations

import base64
import logging
import shlex
import time
from dataclasses import dataclass

from django.conf import settings

import docker
from opentelemetry import trace
from .strategy import get_runner

tracer = trace.get_tracer("dtae.executor")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CodeExecutionResult:
    """Normalized result from a single sandboxed run with resource telemetry."""

    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    wall_clock_duration: float = 0.0
    cpu_time: float = 0.0
    peak_memory: int = 0  # Peak memory usage in bytes


class DockerCodeExecutor:
    """
    Spins up short-lived containers to evaluate candidate code.

    Delegates language-specific setup and validation to LanguageRunner strategies.
    """

    def __init__(
        self,
        timeout_seconds: int | None = None,
        memory_limit_mb: int | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds or settings.DOCKER_EXECUTOR_TIMEOUT_SECONDS
        self.memory_limit = f"{memory_limit_mb or settings.DOCKER_EXECUTOR_MEMORY_MB}m"
        
        docker_host = getattr(settings, "DOCKER_HOST", None)
        if docker_host:
            self._docker_client = docker.DockerClient(base_url=docker_host)
        else:
            self._docker_client = docker.from_env()

    def execute(
        self,
        source_code: str,
        language: str,
        stdin_data: str = "",
    ) -> CodeExecutionResult:
        """
        Run source_code inside an isolated container and capture output/telemetry.

        The container is always removed (--rm equivalent) even on failure.
        """
        with tracer.start_as_current_span("docker.execute") as span:
            span.set_attribute("sandbox.language", language)
            return self._execute_internal(source_code, language, stdin_data)

    def _execute_internal(
        self,
        source_code: str,
        language: str,
        stdin_data: str = "",
    ) -> CodeExecutionResult:
        try:
            runner = get_runner(language)
        except ValueError as exc:
            return CodeExecutionResult(
                stdout="",
                stderr=str(exc),
                exit_code=127,
                timed_out=False,
            )

        # Apply language-specific timeout adjustments
        timeout = self.timeout_seconds * runner.get_timeout_multiplier()

        source_filename = runner.get_source_filename()
        source_file_path = f"/tmp/{source_filename}"
        input_file_path = "/tmp/input.txt"

        # Encode input files to base64 to avoid quoting and character injection issues
        source_b64 = base64.b64encode(source_code.encode("utf-8")).decode("utf-8")
        stdin_b64 = base64.b64encode(stdin_data.encode("utf-8")).decode("utf-8")

        # Compile container execution command sequence
        commands = [
            f"echo '{source_b64}' | base64 -d > {source_file_path}",
            f"echo '{stdin_b64}' | base64 -d > {input_file_path}",
        ]

        compile_cmd_list = runner.get_compile_command(source_file_path, "/tmp")
        if compile_cmd_list:
            compile_cmd_str = " ".join(shlex.quote(arg) for arg in compile_cmd_list)
            commands.append(compile_cmd_str)

        execute_cmd_list = runner.get_execute_command(source_file_path, "/tmp")
        execute_cmd_str = " ".join(shlex.quote(arg) for arg in execute_cmd_list)
        commands.append(f"{execute_cmd_str} < {input_file_path}")

        # Combine commands into a single shell script chain
        container_cmd = ["sh", "-c", " && ".join(commands)]

        timed_out = False
        container = None
        start_time = time.perf_counter()
        start_startup = time.perf_counter()

        try:
            container = self._docker_client.containers.run(
                image=runner.sandbox_image(),
                command=container_cmd,
                detach=True,
                mem_limit=self.memory_limit,
                network_disabled=True,
                read_only=True,
                security_opt=["no-new-privileges"],
                cap_drop=["ALL"],
                pids_limit=64,
                tmpfs={"/tmp": "rw,size=64m"},
                user="nobody",
            )

            startup_duration = time.perf_counter() - start_startup
            try:
                from config.prometheus_middleware import SANDBOX_STARTUP_TIME
                SANDBOX_STARTUP_TIME.labels(language=runner.language).observe(startup_duration)
            except Exception:
                pass

            try:
                exit_result = container.wait(timeout=timeout)
                exit_code = exit_result.get("StatusCode", 1)
            except Exception:
                timed_out = True
                try:
                    container.kill()
                except Exception:
                    pass
                exit_code = 124

            wall_clock_duration = time.perf_counter() - start_time
            try:
                from config.prometheus_middleware import SANDBOX_EXECUTION_DURATION, EXECUTION_STATUS_TOTAL
                SANDBOX_EXECUTION_DURATION.labels(language=runner.language).observe(wall_clock_duration)
                status_lbl = "success" if exit_code == 0 and not timed_out else ("timeout" if timed_out else "failure")
                EXECUTION_STATUS_TOTAL.labels(language=runner.language, status=status_lbl).inc()
            except Exception:
                pass

            # Gather resource telemetry stats prior to removing the container
            cpu_time = 0.0
            peak_memory = 0
            try:
                stats = container.stats(stream=False)
                if "memory_stats" in stats and "max_usage" in stats["memory_stats"]:
                    peak_memory = stats["memory_stats"]["max_usage"]
                if "cpu_stats" in stats and "cpu_usage" in stats["cpu_stats"]:
                    cpu_usage_ns = stats["cpu_stats"]["cpu_usage"].get("total_usage", 0)
                    cpu_time = cpu_usage_ns / 1_000_000_000.0
            except Exception as e:
                logger.warning("Failed to collect container telemetry metrics: %s", e)

            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

        except docker.errors.ImageNotFound:
            try:
                from config.prometheus_middleware import CONTAINER_FAILURES
                CONTAINER_FAILURES.labels(language=runner.language, reason="image_not_found").inc()
            except Exception:
                pass
            logger.error("Sandbox image not found: %s", runner.sandbox_image())
            return CodeExecutionResult(
                stdout="",
                stderr=f"Sandbox image '{runner.sandbox_image()}' not available.",
                exit_code=127,
                timed_out=False,
            )
        except Exception as e:
            try:
                from config.prometheus_middleware import CONTAINER_FAILURES
                CONTAINER_FAILURES.labels(language=runner.language, reason=type(e).__name__).inc()
            except Exception:
                pass
            raise
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

        # Normalize stdout and stderr according to language specifics
        norm_stdout, norm_stderr = runner.normalize_outputs(stdout, stderr)

        return CodeExecutionResult(
            stdout=norm_stdout,
            stderr=norm_stderr,
            exit_code=exit_code,
            timed_out=timed_out,
            wall_clock_duration=wall_clock_duration,
            cpu_time=cpu_time,
            peak_memory=peak_memory,
        )

# Refactor: Update validation checks and constraints.
