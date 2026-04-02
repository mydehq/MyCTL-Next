# Performance Benchmarks: Client Implementation Comparison

To ensure MyCTL meets its "Lean Client" design goal, we conducted extensive performance benchmarking across different client implementations. This document captures the results of these tests and justifies the selection of Go (Cobra) as the primary production client.

## Methodology

The benchmarks measure two critical performance metrics across three client implementations:

1.  **Cold Boot**: The time taken to launch the Python daemon, synchronize the environment via `uv`, fetch the command schema, and execute a simple command (`version`).
2.  **Warm Run**: The time taken to execute a command when the Python daemon is already active in the background. This measures the pure overhead of the client's startup and IPC layer.

### Implementations Tested

| Implementation         | Tooling                 | CLI Engine             |
| :--------------------- | :---------------------- | :--------------------- |
| **Go (Production)**    | Go 1.24+                | `spf13/cobra`          |
| **Python (Optimized)** | Python 3.14 / `.venv`   | `argparse` (Fast-Path) |
| **Python (Compiled)**  | Nuitka 4.0 (Standalone) | `argparse` (Fast-Path) |

## Results Summary

The following results were averaged over 5 iterations on a standard Linux environment.

| Client Implementation | Cold Boot (Avg) | Warm Run (Avg) | Performance Gap (Warm) |
| :-------------------- | :-------------- | :------------- | :--------------------- |
| **Go (Cobra)**        | 4,677 ms        | **6.12 ms**    | **Baseline**           |
| **Python (venv)**     | **4,633 ms**    | 38.45 ms       | ~6x Slower             |
| **Python (uv run)**   | 4,628 ms        | 76.38 ms       | ~12x Slower            |
| **Python (Nuitka)**   | 4,932 ms        | 208.09 ms      | ~34x Slower            |

## Key Findings

### 1. The 6ms Benchmark

The Go implementation achieves near-native performance for warm runs. The 6ms latency includes dialing the Unix socket, fetching a 3KB JSON schema, inflating the CLI tree, and receiving the response. This is essentially unnoticeable to the user, fulfilling the "Logic-Less Client" promise.

### 2. Python Startup Overhead

Despite aggressive optimization (Lazy Imports and Fast-Path proxying), the Python interpreter introduces a minimum overhead of ~30-40ms. While small, this is a 6x increase over Go. When wrapped in `uv run`, the overhead jumps to ~75ms due to environment resolution logic.

### 3. Nuitka "Onefile" Latency

The Nuitka-compiled standalone binary proved to be the slowest in warm runs (~200ms). This is due to the inherent overhead of the "onefile" self-extractor and the initialization of the embedded Python runtime for every execution. For a "Lean Client" that performs frequent, short-lived tasks, this initialization cost is prohibitive.

## ⚖️ Final Architecture Decision

Based on these results, **Go remains the primary language for the MyCTL Client**. It provides the $O(1)$ proxy performance required for a high-performance system controller. The Python implementation remains a valuable reference for experimental workflows but is not suitable for the performance-critical path.
