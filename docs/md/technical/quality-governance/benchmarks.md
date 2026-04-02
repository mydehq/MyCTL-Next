# Client Performance Benchmarks

This page explains why the MyCTL client is written in Go and what the measured startup costs look like.

The client is intentionally thin. Its job is to:

- start fast
- fetch schema from the daemon
- forward commands over IPC
- render the response

That means the client’s runtime cost has to stay close to the cost of the IPC round trip itself.

---

## 1. What Was Measured

The benchmark compares cold and warm command execution across different client implementations.

### Cold Boot

Cold boot measures the full startup path:

- launch the daemon if needed
- sync the environment
- fetch the schema
- execute a simple command

### Warm Run

Warm run measures the client overhead when the daemon is already running.

That is the number that matters most for the day-to-day user experience, because it isolates client startup and IPC cost.

---

## 2. Implementations Compared

The benchmark compared three client shapes:

| Implementation         | Tooling                 | CLI Engine             |
| :--------------------- | :---------------------- | :--------------------- |
| **Go (Production)**    | Go 1.24+                | `spf13/cobra`          |
| **Python (Optimized)** | Python 3.14 / `.venv`   | `argparse` (Fast-Path) |
| **Python (Compiled)**  | Nuitka 4.0 (Standalone) | `argparse` (Fast-Path) |

The comparison is not about language preference. It is about the cost of startup and the cost of being the persistent command proxy.

---

## 3. Results

The tests were averaged across 5 iterations on a standard Linux environment.

| Client Implementation | Cold Boot (Avg) | Warm Run (Avg) | Warm Gap    |
| :-------------------- | :-------------- | :------------- | :---------- |
| **Go (Cobra)**        | 4,677 ms        | **6.12 ms**    | baseline    |
| **Python (venv)**     | **4,633 ms**    | 38.45 ms       | ~6x slower  |
| **Python (uv run)**   | 4,628 ms        | 76.38 ms       | ~12x slower |
| **Python (Nuitka)**   | 4,932 ms        | 208.09 ms      | ~34x slower |

The important row is the warm run. That is the steady-state client experience.

---

## 4. What The Numbers Mean

### Go Warm Runs Are Effectively Instant

The Go client stays near the IPC cost. It dials the socket, fetches schema, inflates the CLI, and prints the result with very little overhead.

That is the main reason it is the production client.

### Python Adds Startup Overhead

Even with optimization, Python startup and environment resolution add noticeable delay. That extra time is small in absolute terms but large compared to the Go path.

### Compiled Python Still Pays Runtime Costs

Even when compiled, the Python client still pays for embedded runtime initialization and packaging overhead.

That makes it a poor fit for a client that is expected to start constantly and finish quickly.

---

## 5. Why This Matters Architecturally

The daemon does the work. The client should only proxy it.

If the client starts too slowly, the whole system feels heavier than it needs to be, even when the daemon is efficient.

That is why the client is a lean Go binary and the daemon remains the execution engine.

---

## 6. Operational Conclusion

The benchmark results support one architecture:

- Go for the production client
- Python for the daemon and plugin runtime
- schema-driven CLI inflation over IPC

That keeps the client small and predictable while leaving real work in the daemon.
