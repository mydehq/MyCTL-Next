// Consts in this will be available throughout the documentation site.
// Access them with {{metadata.*}} or <a :href="metadata.*">*</a>
export const metadata = {
  title: "MyCTL Next",
  description: "A Powerful CLI to control your Desktop!",
  repo: "https://github.com/mydehq/MyCTL",
  miseHome: "https://mise.jdx.dev/getting-started",

  // 📦 Versions & Requirements
  versions: {
    python_min: "3.13+",
    api_ver: "2.5.0",
  },

  // 🏗 Infrastructure Paths
  paths: {
    venv: "~/.local/share/myctl/venv",
    plugins: "~/.local/share/myctl/plugins",
    socket: "$XDG_RUNTIME_DIR/myctl/myctld.sock",
    logs: "$XDG_STATE_HOME/myctl/daemon.log",
  },

  // 🛠 Tools & Ecosystem
  tools: {
    uv: "https://docs.astral.sh/uv/",
    go: "https://go.dev/",
    cobra: "https://cobra.dev/",
  },
};
