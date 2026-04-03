# Adding Commands & Flags

This page documents how to register commands and flags in a plugin using the `{{metadata.pkgs.sdk}}` SDK.

> [!IMPORTANT] Signature-driven API
> Define your command inputs as regular function parameters.  
> The SDK reads the function signature, builds the CLI, and injects parsed, typed values into your handler.

---

## TODO: Add support for [arguments](https://typer.tiangolo.com/tutorial/arguments/optional/#make-an-optional-cli-argument)

## Also Plugin optional/required is not implemented yet.

--

## Prerequisites

Before registering any handler, initialize your `Plugin` instance in `main.py`.

```python
from {{metadata.pkgs.sdk}} import Plugin, Context, flag

plugin = Plugin()
```

## Registering Commands

### Root Command

Use the `@plugin.root` decorator to register the **primary entry point for your plugin**.
<br>
**There should & must have only one root command per plugin**

```python
# Command: `{{metadata.pkgs.sdk}} <plugin>`
@plugin.root
async def main(ctx: Context):
    return ctx.ok("Plugin is active")
```

### Sub Commands

Use the `@plugin.command` decorator to define sub-actions.

```python
# Command: `{{metadata.pkgs.sdk}} <plugin> list`
@plugin.command("list", help="List available resources")
async def list_resources(ctx: Context):
    ...
```

---

## Defining Flags

Flags are defined as **function parameters** using the `flag()` helper as a default value.

`name: type = flag(short, *, default, help, ...)`

- **`short`**: Short alias (e.g., `"p"` -> `-p`).
- **`help`**: Usage description shown in CLI help.
- **`default`**: Default value if the flag is omitted.
- **`choices`**: Allowed values for the flag.
- **`flag_type`**: Optional explicit type override (rarely needed).

---

### Examples

#### 1. Optional Flag (with Default value)

**Provide a default** to make the flag optional. The SDK casts the CLI value to the annotated type.

```python
@plugin.command("serve", help="Run HTTP server")
async def serve(ctx: Context, port: int = flag("p", default=8080, help="Port to bind")):
    # 'port' is injected as an int
    log.info(f"Serving on port {port}")
    ...
```

**User experience:**

- `{{metadata.pkgs.sdk}} myplugin serve` → `port = 8080`
- `{{metadata.pkgs.sdk}} myplugin serve --port 9090` → `port = 9090`

#### 2. Required Flag

Omit `default` to mark the flag required (recommended):

```python
@plugin.command("report", help="Generate a report")
async def generate_report(ctx: Context, output: str = flag("o", help="Output path")):
    # Engine validates presence of --output before calling your handler
    ...
```

If the client does not pass `--output` the Engine will respond with a helpful error like:

```
missing required flag: --output
```

#### 3. Boolean Toggle (Switch)

Define a boolean default to create a toggle flag.

```python
@plugin.command("cleanup", help="Clean temporary files")
async def cleanup(ctx: Context, force: bool = flag("f", default=False, help="Force execution")):
    if force:
        log.warning("Force mode enabled")
    ...
```

**User experience:**

- `{{metadata.pkgs.sdk}} myplugin cleanup` → `force = False`
- `{{metadata.pkgs.sdk}} myplugin cleanup --force` → `force = True`

#### 4. Flag with Choices

Restrict allowed inputs to a specific set of values.

```python
@plugin.command("show", help="Show system info")
async def show(
    ctx: Context,
    style: str = flag("s", default="text", choices=["text", "json"], help="Output format")
):
    ...
```

---

### Smart Type Inference

Type inference priority:

1. Parameter annotation (recommended)
2. Default value type (when present and not Ellipsis)
3. Fallback to `str`

Example:

```python
# Best: explicit annotation
count: int = flag("c", default=1, help="Retry count")

# If annotation missing, inference falls back to default value
limit = flag("l", default=10, help="Limit count")  # inferred as int
```

---

## Complete Example

```python
from {{metadata.pkgs.sdk}} import Plugin, Context, flag, log

plugin = Plugin()

@plugin.root
async def main(
    ctx: Context,
    # Trigger flag, optional with default
    verbose: bool = flag("v", default=False, help="Verbose output"),
    # optional with default
    count: int = flag("c", default=1, help="Retry count"),
    # required (concise)
    config: str = flag("C", help="Path to configuration file"),
) -> Dict:
    if verbose:
        log.info("Starting operation", count=count)

    # 'config' is guaranteed present (or the Engine returned an error earlier)
    return ctx.ok({"executed": True, "count": count})

@plugin.command("hi", help="Prints hi message")
async def say_hi(
  ctx: Context,
  # required
  name: str = flag("n", help="Users name"),
) -> Dict:
    ctx.ok()
```
