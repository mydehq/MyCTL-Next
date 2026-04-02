// Consts in this will be available throughout the documentation site.
// Access them with {{metadata.*}} or <a :href="metadata.*">*</a>
export const metadata = {
  title: "MyCTL Next",
  description: "A Powerful CLI to control your Desktop!",
  repo: "https://github.com/mydehq/MyCTL",
  miseHome: "https://mise.jdx.dev/getting-started",

  // 📦 Versions & Requirements
  versions: {
    python_min: "3.14+",
    api: "2.5.0",
  },

  // 🏗 Infrastructure Paths
  // Use shared constants: APP_NAME=myctl, DAEMON_NAME=myctld.
  paths: {
    venv: "$XDG_DATA_HOME/myctl/venv",
    plugins: "$XDG_DATA_HOME/myctl/plugins",
    socket: "$XDG_RUNTIME_DIR/myctl/myctld.sock", // daemon socket
    logs: "$XDG_STATE_HOME/myctl/myctld.log", // daemon log file
  },

  // 🛠 Tools & Ecosystem
  tools: {
    uv: "https://docs.astral.sh/uv/",
    go: "https://go.dev/",
    cobra: "https://cobra.dev/",
  },
};
