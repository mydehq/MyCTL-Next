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

  title: metadata.title,
  description: metadata.description,

  transformPageData(pageData) {
    pageData.frontmatter.metadata = metadata;
    if (pageData.relativePath === "index.md") {
      pageData.frontmatter.hero.name = metadata.title;
      pageData.frontmatter.hero.text = metadata.description;
      pageData.frontmatter.hero.tagline = metadata.tagline;
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
      { text: "Technical", link: "/technical/overview" },
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
              { text: "Commands & Flags", link: "/dev/plugin-sdk/commands" },
              { text: "Lifecycle & Tasks", link: "/dev/plugin-sdk/lifecycle" },
              { text: "API Reference", link: "/dev/plugin-sdk/api" },
            ],
          },
          { text: "Server API (IPC)", link: "/dev/server-api" },
        ],
      },
      {
        text: "Technical Reference",
        collapsed: true,
        items: [
          { text: "Overview", link: "/technical/overview" },
          { text: "Refactor", link: "/technical/daemon-architecture-vision" },
        ],
      },
    ],

    socialLinks: [{ icon: "github", link: metadata.repo }],
  },
});
