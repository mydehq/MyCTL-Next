# Permission Model

This page explains the capability model MyCTL is expected to grow into around plugin execution.

The current codebase already validates plugins by identity and metadata. The permission model goes one step further: it decides what a plugin is allowed to do after it loads.

---

## 1. Why A Permission Model Exists

Plugins run inside the daemon process, so the daemon needs a way to control what a plugin may access.

A permission model lets the runtime answer questions like:

- may this plugin read system info?
- may it send notifications?
- may it use audio APIs?
- may it make network requests?
- may it execute shell commands?

The goal is not to stop plugins from existing. The goal is to make risky operations explicit.

---

## 2. Capability Shape

The planned model is capability-based.

That means plugins declare the capabilities they need, and the daemon decides whether those capabilities are allowed.

Examples of capabilities:

- `system_info` for read-only metrics
- `notifications` for desktop notifications
- `audio` for audio control APIs
- `network` for outbound HTTP or network access
- `shell_exec` for command execution

Some capabilities are low risk. Others are high risk and would need stronger user consent.

---

## 3. Enforcement Layers

The permission model is expected to work at more than one layer.

### Manifest Layer

The plugin would declare needed capabilities in its package metadata.

### Import Layer

The daemon could deny imports that belong to blocked capability areas.

### API Layer

SDK helpers could verify capability state before running sensitive actions.

The point of having multiple layers is to avoid a single bypass point.

---

## 4. Expected User Experience

The runtime should make the decision visible.

Possible outcomes:

- low-risk plugin loads normally
- high-risk plugin asks for explicit consent
- denied plugin gets a clear error and does not activate

That gives users a visible trust boundary instead of silent permission behavior.

---

## 5. Current Reality

Today, MyCTL already does some of the groundwork:

- plugin identity validation
- discovery and load isolation
- error handling during plugin load

What is not implemented yet is the full capability pipeline.

That means the permission model is still a future design area, not a runtime feature.

---

## 6. How This Fits The Rest Of The System

The permission model sits on top of plugin discovery and plugin loading.

It does not replace those systems. It adds a policy layer between “plugin is valid” and “plugin is allowed to run sensitive operations.”

That is why the related docs are:

- [Plugin Discovery](../plugin-system/plugin-discovery.md)
- [Plugin Loading](../plugin-system/plugin-loading.md)

Those pages explain the current runtime mechanics. This page explains the control layer that can be added on top.

---

## 7. Summary

The permission model is the capability boundary for plugins.

The current implementation validates and loads plugins. The planned model decides what a loaded plugin may do.

That is the internal direction the system is designed for.
