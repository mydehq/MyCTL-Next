"""MyCTL daemon engine package.

This package hosts runtime modules for socket IPC, command routing,
plugin discovery/loading, and daemon lifecycle management.

All modules use postponed annotation evaluation via
``from __future__ import annotations`` for consistent typing behavior.
"""
