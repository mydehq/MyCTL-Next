# SDK Specification (Protocols)

To ensure the MyCTL SDK (`myctl`) is small and fast, it is built using **Python Protocols**. A Protocol is like an "interface" or a "blueprint" that defines what a class should look like, without providing the actual code.

## 1. Why Protocols?

By using Protocols, the SDK doesn't need to import any part of the Engine. It just says: "A `Context` object must have an `ok()` method." When the Engine runs a plugin, it passes its *own* real `Context` object, which follows that blueprint.

- **Zero-Dependency**: The `myctl` package is self-contained.
- **Fast Import**: Incredibly quick to load in the Python interpreter.
- **Easy Testing**: Plugin authors can mock these objects easily for unit tests.

---

## 2. Core Protocols

### The `Context` Interface
This is the object passed to every plugin command handler.

| Method / Attribute | Signature | Role |
| :--- | :--- | :--- |
| `args` | `list[str]` | Positional arguments from the user. |
| `flags` | `dict[str, Any]` | Map of flag names to values. |
| `terminal` | `TerminalContext` | Screen width, height, and TTY status. |
| `ok(data)` | `-> Response` | Return a success response. |
| `err(msg)` | `-> Response` | Return a failure response. |
| `ask(prompt)` | `-> Awaitable[str]` | Trigger an interactive prompt. |

### The `Response` Interface
The standard format for all Engine IPC replies.

```python
class Response(Protocol):
    status: int       # 0=OK, 1=ERROR, 2=ASK
    data: Any         # The payload (string, dict, list)
    exit_code: int    # The OS exit code (0 or 1)
```

### The `StyleHelper` Interface
Used for consistent, pretty terminal output.

*   `bold(text)`: Make text bold.
*   `success(text)`: Format text as green/success.
*   `warning(text)`: Format text as yellow/warning.
*   `table(rows, headers)`: Format data as a clean CLI table.

---

## 3. The `SystemContext` (Engine Only)

The `SystemContext` is a specialized implementation that is **invisible to the SDK Protocols**. It only exists inside the Engine (`myctld`) to allow privileged commands to control the daemon.

### Admin-Only Methods
- `request_shutdown(reason)`
- `reload_plugins()`
- `get_registry()`

Plugins can never access these methods because they are not part of the `Context` Protocol defined in the SDK.

---

## 4. Key Implementation Details

*   **File**: `daemon/myctl/context.py`
*   **Module**: `typing.Protocol`
*   **Enforcement**: The Engine uses `isinstance`-like checks at runtime (structural typing) to ensure that only objects following these specifications are passed to handlers.
