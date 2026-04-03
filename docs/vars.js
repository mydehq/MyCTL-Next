// Consts in this will be available throughout the documentation site.
// Access them with {{metadata.*}} or <a :href="metadata.*">*</a>
export const metadata = {
  project: {
    title: "MyCTL Next",
    desc: "A Powerful CLI to control your Desktop!",
    repo: "https://github.com/mydehq/MyCTL",
  },

  // Versions & Requirements
  versions: {
    python_min: "3.14+",
    api: "3.0.0", // V3 Modern SDK
  },

  // SDK Specification (V3)
  pkgs: {
    sdk: "myctl",
    daemon: "myctld",
  },

  // Infrastructure Paths
  paths: {
    venv: "$XDG_DATA_HOME/myctl/venv",
    plugins: "$XDG_DATA_HOME/myctl/plugins",
    socket: "$XDG_RUNTIME_DIR/myctl/myctld.sock", // daemon socket
    logs: "$XDG_STATE_HOME/myctl/myctld.log", // daemon log file
  },

  // Tools & Ecosystem
  tools: {
    uv: "https://docs.astral.sh/uv/",
    go: "https://go.dev/",
    cobra: "https://cobra.dev/",
    mise: "https://mise.jdx.dev/getting-started",
    brv_srch: "https://search.brave.com/ask?q=",
  },
};
