import { metadata } from "../../vars.js";

/**
 * A Markdown-It plugin that replaces {{metadata.*}} placeholders with 
 * values from the global vars.js file. Runs during the core 'normalize' 
 * phase to ensure replacements happen before links or code blocks are parsed.
 */
export function metadataPlugin(md) {
  md.core.ruler.before("normalize", "metadata_replace", (state) => {
    state.src = state.src.replace(/{{metadata\.([\w.]+)}}/g, (match, path) => {
      const parts = path.split(".");
      let val = metadata;
      
      for (const part of parts) {
        if (val && typeof val === "object") {
          val = val[part];
        } else {
          return match;
        }
      }
      
      return val !== undefined ? val : match;
    });
  });
}
