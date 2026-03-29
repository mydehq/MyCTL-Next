import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  srcDir: "md",
  
  title: "MyCTL",
  description: "The Unified Linux Desktop CLI",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/architecture' },
      { text: 'SDK', link: '/plugin-sdk' }
    ],

    sidebar: [
      {
        text: 'Core Concepts',
        items: [
          { text: 'System Architecture', link: '/architecture' },
          { text: 'Bootstrapping Lifecycle', link: '/bootstrapping' },
          { text: 'IPC Protocol', link: '/ipc-protocol' }
        ]
      },
      {
        text: 'Extension & SDK',
        items: [
          { text: 'Command Discovery', link: '/discovery' },
          { text: 'Plugin SDK Guide', link: '/plugin-sdk' }
        ]
      },
      {
        text: 'Examples',
        items: [
          { text: 'Markdown Examples', link: '/markdown-examples' },
          { text: 'Runtime API Examples', link: '/api-examples' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/mydehq/MyCTL' }
    ]
  }
})
