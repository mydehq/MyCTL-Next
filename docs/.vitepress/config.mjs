import { withMermaid } from "vitepress-plugin-mermaid";
import { metadata } from "../vars.js";
import { metadataPlugin } from "./plugins/metadata.js";

export default withMermaid({
  srcDir: "md",
  cleanUrls: true,
  vite: {
    publicDir: "../public",
  },
  markdown: {
    config: (md) => {
      md.use(metadataPlugin);
    },
  },

  head: [["link", { rel: "icon", type: "image/svg+xml", href: "/icon.svg" }]],

  title: metadata.project.title,
  description: metadata.project.desc,

  transformPageData(pageData) {
    pageData.frontmatter.metadata = metadata;
    if (pageData.relativePath === "index.md") {
      pageData.frontmatter.hero.name = metadata.project.title;
      pageData.frontmatter.hero.text = metadata.project.desc;
      // Intentionally not overwriting tagline so the one in index.md shines through
    }
  },

  themeConfig: {
    logo: "/icon.svg",
    outline: [2, 3],

    search: {
      provider: "local",
      options: {
        miniSearch: {},
      },
    },

    nav: [
      { text: "Getting Started", link: "/guide/getting-started" },
      { text: "Plugin SDK", link: "/dev/plugin-sdk" },
      { text: "Technical", link: "/technical/" },
    ],

    sidebar: [
      {
        text: "User Guide",
        items: [
          { text: "Installation", link: "/guide/install" },
          { text: "Getting Started", link: "/guide/getting-started" },
          { text: "Command Reference", link: "/guide/command-reference" },
          { text: "Project Roadmap", link: "/roadmap" },
        ],
      },
      {
        text: "Developer Guide",
        items: [
          {
            text: "Plugin Development",
            collapsed: true,
            items: [
              { text: "Introduction", link: "/dev/plugin-sdk/" },
              { text: "Quick Start", link: "/dev/plugin-sdk/quick-start" },
              { text: "Manifest Reference", link: "/dev/plugin-sdk/manifest" },
              {
                text: "Adding Commands & Flags",
                link: "/dev/plugin-sdk/adding-handlers",
              },
              { text: "Hooks & Tasks", link: "/dev/plugin-sdk/hooks" },
              { text: "API Reference", link: "/dev/plugin-sdk/api" },
            ],
          },
          { text: "System Commands", link: "/dev/system-commands" },
          { text: "Client API (IPC)", link: "/dev/client-api" },
        ],
      },
      {
        text: "Technical Reference",
        collapsed: false,
        items: [
          { text: "Overview", link: "/technical/" },
          {
            text: "Core Architecture",
            collapsed: true,
            items: [
              {
                text: "System Blueprint",
                link: "/technical/core/architecture",
              },
              {
                text: "Engine Runtime",
                link: "/technical/core/runtime",
              },
              {
                text: "Engine Bootstrapping",
                link: "/technical/core/bootstrapping",
              },
              {
                text: "Engine Services",
                link: "/technical/core/services",
              },
              {
                text: "IPC Protocol",
                link: "/technical/core/ipc-protocol",
              },
            ],
          },
          {
            text: "Command Registry",
            collapsed: true,
            items: [
              {
                text: "Routing & Dispatch",
                link: "/technical/registry/dispatch",
              },
              {
                text: "Schema Inflation",
                link: "/technical/registry/schemas",
              },
            ],
          },
          {
            text: "Plugin System",
            collapsed: true,
            items: [
              {
                text: "Discovery & Tiers",
                link: "/technical/plugins/discovery",
              },
              {
                text: "Security & Guard",
                link: "/technical/plugins/security",
              },
            ],
          },
          {
            text: "SDK Specification",
            collapsed: true,
            items: [
              {
                text: "Protocols (Interfaces)",
                link: "/technical/sdk/protocols",
              },
            ],
          },
        ],
      },
    ],

    socialLinks: [{ icon: "github", link: metadata.project.repo }],
  },
});
