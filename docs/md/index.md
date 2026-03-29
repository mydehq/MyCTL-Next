---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "MyCTL"
  text: "The Unified Linux Desktop Controller."
  tagline: "A Lean Go Proxy meets an Intelligent Python Daemon. Sub-millisecond speeds, infinite N-level nesting, and pro-grade SDKs."
  actions:
    - theme: brand
      text: "Read the Architecture"
      link: /architecture
    - theme: alt
      text: "View Plugin SDK"
      link: /plugin-sdk

features:
  - title: "⚡️ Sub-ms Proxy"
    details: "The Go client is a pure O(1) tunnel, stripping all Cobra logic for lightning-fast command execution."
  - title: "🐍 Intelligent Daemon"
    details: "A self-bootstrapping Python server that creates its own isolated sandbox and manages system state persistently."
  - title: "🧩 Infinite Nesting"
    details: "Deeply nested hierarchical commands like 'audio sink mute' are natively supported through our N-Level registry."
  - title: "🛠️ SDK-First Design"
    details: "The 'myctl.api' package provides a curated developer experience with full IDE type-hinting and autocompletion."
---
