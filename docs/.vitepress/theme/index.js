import DefaultTheme from "vitepress/theme";
import { inject } from "@vercel/analytics";
import "./style.css";
import { metadata } from "../../vars.js";

/** @type {import('vitepress').Theme} */
export default {
  extends: DefaultTheme,
  // This is the entry point for your custom theme.
  // You can extend the default theme using Vue slots or global components.
  enhanceApp({ app, router, siteData }) {
    // Register metadata as a global property for Docusaurus-like shared variables
    app.config.globalProperties.metadata = metadata;
    if (!import.meta.env.SSR) {
      inject();
    }
  },
};
