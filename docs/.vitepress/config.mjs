import { withMermaid } from "vitepress-plugin-mermaid";
import { metadata } from "../vars.js";

export default withMermaid({
  srcDir: "md",
  cleanUrls: true,
  vite: {
    publicDir: "../public",
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
          { text: "Developing Plugins", link: "/dev/plugin-sdk" },
          { text: "Server API (IPC)", link: "/dev/server-api" },
        ],
      },
      {
        text: "Technical Reference",
        items: [
          { text: "Overview", link: "/technical/overview" },
          { text: "System Architecture", link: "/technical/architecture" },
          { text: "Bootstrapping", link: "/technical/bootstrapping" },
          { text: "IPC Protocol", link: "/technical/ipc-protocol" },
          { text: "Core Engine & Registry", link: "/technical/registry" },
          { text: "Plugin Discovery", link: "/technical/plugin-discovery" },
          { text: "Plugin Lifecycle", link: "/technical/lifecycle" },
          { text: "Permission System", link: "/technical/permissions" },
        ],
      },
    ],

    socialLinks: [{ icon: "github", link: metadata.repo }],
  },
});
