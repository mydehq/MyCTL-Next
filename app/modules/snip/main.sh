
#============= Configuration =============#

SNIP_DEFAULT_MODE="$(read-hconf default_ss_mode)"
SNIP_CAPTURE_CMD="grimblast --freeze save"
SNIP_FILE="$(read-hconf ss_save_path)/$(read-hconf ss_file_name).png"
SNIP_EDITOR_CMD="satty --filename - --output-filename"

#================ Functions ==============#

declare -rx SNIP_DEFAULT_MODE SNIP_CAPTURE_CMD SNIP_FILE SNIP_EDITOR_CMD

declare -a MYCTL_META MYCTL_PERMS MYCTL_USAGE

MYCTL_META=(
    [id]="snip"
    [ver]="0.1.0"
    [desc]="Get Screenshot of Monitor/window/selection"
)

MYCTL_PERMS=(
    ""
)

MYCTL_USAGE=(
    [j, --json]="Output json"
)

echo "${MYCTL_USAGE[@]}"

main() {
    local mode="${1:-area}" \
          default_mode="$SNIP_DEFAULT_MODE" \
          snip_cmd="$SNIP_CAPTURE_CMD" \
          edit_cmd="$SNIP_EDITOR_CMD"  \
          snip_file="$SNIP_FILE"       \
          final_cmd

    case "$mode" in
        "") mode="$default_mode"
            ;;
        area) mode="area"
            ;;
        active) mode="active"
            ;;
        screen) mode="screen"
            ;;
        *) log.fatal "Invalid mode: $mode"
            ;;
    esac

    log.debug "Mode: $mode"
    log.debug "Output file: $snip_file"
    log.debug "Snipping command: $snip_cmd $mode -"
    log.debug "Editor command: $edit_cmd"

    final_cmd="$snip_cmd $mode - | $edit_cmd $snip_file"  && log.debug "Final command: $final_cmd"

    if ! eval "$final_cmd"; then
        log.fatal "Failed to capture screenshot"
    fi
}
