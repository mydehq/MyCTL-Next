# Plugin Discovery

This page explains how MyCTL finds plugins on disk and decides which ones are eligible to load.

Discovery is a file-system and metadata problem. The daemon scans configured locations, validates each candidate, and hands only the valid ones to the loader.

---

## 1. Discovery Order

MyCTL scans plugin directories in priority order:

1. development path: project `plugins/`
2. user path: `$XDG_DATA_HOME/myctl/plugins`
3. system path: `/usr/share/myctl/plugins`

Earlier paths win.

That means a local development plugin can shadow an installed system plugin with the same ID.

---

## 2. Plugin ID Rules

The plugin ID is the directory name.

If two plugins share the same ID, the higher-priority one wins and the lower-priority one is ignored.

Example:

- `plugins/audio/` wins over `/usr/share/myctl/plugins/audio/`
- the daemon keeps the first valid match in priority order
- later duplicates are skipped intentionally

This is how MyCTL keeps development overrides predictable.

---

## 3. Validation Before Load

Before importing a plugin, the daemon checks that the candidate is structurally valid.

The checks are straightforward:

1. the directory exists
2. `pyproject.toml` exists
3. `[project].name` matches the folder name exactly
4. declared API compatibility is acceptable

If validation fails, the plugin is skipped and the reason is logged.

This prevents broken metadata from reaching the loader.

---

## 4. Discovery Pipeline

Discovery is not loading. It only decides which candidates are worth loading.

The flow is:

1. scan all configured plugin tiers
2. normalize each candidate directory into metadata
3. validate the manifest and identity
4. keep the first valid plugin for each ID
5. pass the final set to the loader

That separation is important because the loader handles Python import state, while discovery handles filesystem and manifest state.

---

## 5. Dependency Sync Handoff

If a plugin declares dependencies, discovery marks it as loadable but does not install anything itself.

The actual sync step happens immediately before import during loading.

That means discovery only answers:

- is this plugin candidate structurally valid?
- should this candidate win for its ID?
- should this candidate move forward to loading?

---

## 6. What Discovery Does Not Do

Discovery does not:

- import `main.py`
- dispatch commands
- run lifecycle hooks
- render CLI output
- manage IPC requests

Those responsibilities belong to the loader, registry, and client layers.

---

## 7. Why The Priority Model Exists

Priority ordering makes local development practical.

You can keep a working copy of a plugin in the project tree and shadow the installed version without changing any daemon configuration.

That is better than requiring explicit override flags for every local test run.

---

## 8. Debugging Discovery

If a plugin does not show up, check:

- the folder is in one of the configured discovery tiers
- the folder name matches `[project].name`
- the directory contains a manifest
- the manifest parses successfully
- the plugin is not shadowed by a higher-priority sibling

If a plugin is discovered but not loaded, the problem is usually in validation or dependency sync, not discovery itself.

---

## 9. Summary

Plugin discovery decides which plugin directories should move forward into loading.

It handles:

- search paths
- priority order
- shadowing
- validation

It does not handle import, dispatch, or runtime execution.



