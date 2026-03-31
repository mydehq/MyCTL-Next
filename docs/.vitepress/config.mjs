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
    if (pageData.relativePath === "index.md") {
      pageData.frontmatter.hero.name = metadata.title;
      pageData.frontmatter.hero.text = metadata.description;
      pageData.frontmatter.hero.tagline = metadata.tagline;
    }
  },

  themeConfig: {
    logo: "/icon.svg",

    nav: [
      { text: "Getting Started", link: "/guide/getting-started" },
      { text: "Plugin SDK", link: "/dev/plugin-sdk" },
      { text: "Architecture", link: "/technical/architecture" },
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
          { text: "System Architecture", link: "/technical/architecture" },
          { text: "IPC Protocol", link: "/technical/ipc-protocol" },
          { text: "Bootstrapping Lifecycle", link: "/technical/bootstrapping" },
          { text: "Plugin Discovery", link: "/technical/plugin-discovery" },
          { text: "Core Engine & Registry", link: "/technical/registry" },
        ],
      },
    ],

    socialLinks: [{ icon: "github", link: metadata.repo }],
  },
});
