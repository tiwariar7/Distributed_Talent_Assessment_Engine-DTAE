# ADR 0001: Sandboxed Code Execution Engine Architecture

## Status
Approved

## Context
Candidates submit code in various languages (Python, JavaScript, C++, Java) that must be compiled and executed on our servers. Since we cannot trust candidate-supplied bytecode/source, executing code directly on the host poses massive security risks, including host compromise, file access, and denial of service.

## Decision
We implement a polymorphic containerized execution model:
1. **Runner Strategy Pattern:** Language-specific concerns (filenames, timeout multipliers, compilation arguments, runtime executions, output normalizations) are encapsulated in `LanguageRunner` classes under `strategy.py`.
2. **Docker Containment:** Code is compiled and run inside short-lived container sandboxes utilizing a consolidated `dtae/multi-sandbox:latest` base image.
3. **Security Hardening constraints:**
   - Ephemeral read-only root filesystems (`read_only=True`).
   - Writeable `tmpfs` mounted at `/tmp` to compile code.
   - Reduced Linux capabilities (`cap_drop=['ALL']`).
   - No privilege escalation (`no-new-privileges` flag).
   - Constrained resources: Memory capped at 128MB, process ID (pid) limits restricted to 64, and network interface completely disabled (`network_disabled=True`).
   - Unprivileged execution user context (`user="nobody"`).
4. **Base64 Shell Pipelining:** Bypasses shell quoting constraints and potential shell injections by transferring code and inputs encoded in Base64 onto the container shell stream, decoding them inside `/tmp` directly prior to compile/execute steps.

## Consequences
- Complete containment of untrusted code.
- Ephemeral execution runs do not leave residual files on host machines.
- Adding new languages requires only subclassing `LanguageRunner` and adding compiler dependencies to the Docker image.


- Note: Align with project code quality guidelines.


- Note: Refactor variable names for better readability.


- Note: Improve error handling and exception logging.


- Note: Enhance component rendering performance.
