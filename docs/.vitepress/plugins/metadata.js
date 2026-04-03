import { metadata } from "../../vars.js";

/**
 * A Markdown-It plugin that replaces {{metadata.*}} placeholders with
 * values from the global vars.js file. Runs during the core 'normalize'
 * phase to ensure replacements happen before links or code blocks are parsed.
 */
export function metadataPlugin(md) {
  md.core.ruler.before("normalize", "metadata_replace", (state) => {
    // 1. Clean up "linked variables" inside mermaid blocks.
    // Replace [Text]({{ metadata.path }}) with just Text so labels stay clean.
    state.src = state.src.replace(
      /```mermaid\s+([\s\S]*?)```/g,
      (mermaidBlock) => {
        return mermaidBlock.replace(
          /\[(.*?)\]\({{\s*metadata\.([\w.]+)\s*}}\)/g,
          "$1",
        );
      },
    );

    // 2. Perform global metadata replacement for all remaining placeholders.
    state.src = state.src.replace(
      /{{\s*metadata\.([\w.]+)\s*}}/g,
      (match, path) => {
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
      },
    );
  });
}
