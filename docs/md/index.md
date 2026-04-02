---
layout: home

hero:
  name: "MyCTL"
  text: "High-Performance Linux Desktop Controller"
  tagline: "A Logic-Less Go Proxy Orchestrating a Persistent Python Engine"
  image:
    src: /icon.svg
    alt: MyCTL Logo

  actions:
    - theme: brand
      text: "Get Started"
      link: /guide/getting-started

    - theme: alt
      text: "Plugin SDK"
      link: /dev/plugin-sdk

features:
  - icon: "🌍"
    title: "Environment Agnostic"
    details: "Runs anywhere. MyCTL works seamlessly across all DEs/WMs"
    link: /guide/install

  - icon: "⚡️"
    title: "Instant Performance"
    details: "Built with client-server architecture, little to no latency."
    link: /guide/getting-started#architecture-the-lean-proxy

  - icon: "🧩"
    title: "Extend with Plugins"
    details: "Add various functionalities beyond builtins with Rich plugin system"
    link: /dev/plugin-sdk

  - icon: "🍱"
    title: "No Dependency Hell"
    details: "Almost Zero system package deps. A fully sandboxed runtime keeps host system clean."
    link: /technical/core-runtime/bootstrapping
---
