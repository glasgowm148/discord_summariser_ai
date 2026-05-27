#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="config/.env"
EXPORTER="${DISCORDCHATEXPORTER_PATH:-DiscordChatExporter/DiscordChatExporter-linux/mac/DiscordChatExporter.Cli.osx-arm64/DiscordChatExporter.Cli}"

if [[ -f "${ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
fi

if [[ -z "${DISCORD_TOKEN:-}" ]]; then
    echo "Error: DISCORD_TOKEN must be set in ${ENV_FILE}."
    exit 1
fi

if [[ ! -x "${EXPORTER}" ]]; then
    echo "Error: DiscordChatExporter not found or not executable:"
    echo "  ${EXPORTER}"
    echo "Set DISCORDCHATEXPORTER_PATH in your shell if it lives elsewhere."
    exit 1
fi

date_utc() {
    date -u "$@"
}

days_ago() {
    local days="$1"
    date -u -v-"${days}"d '+%Y-%m-%d' 2>/dev/null || date -u -d "${days} days ago" '+%Y-%m-%d'
}

one_month_ago() {
    date -u -v-1m '+%Y-%m-%d' 2>/dev/null || date -u -d "1 month ago" '+%Y-%m-%d'
}

start_of_year() {
    date -u '+%Y-01-01'
}

slugify() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-|-$//g'
}

choose_menu() {
    local title="$1"
    local default_index="$2"
    shift 2
    local options=("$@")
    local choice

    echo
    echo "${title}"
    for i in "${!options[@]}"; do
        local marker=" "
        [[ "$((i + 1))" == "${default_index}" ]] && marker="*"
        printf "  %s %d) %s\n" "${marker}" "$((i + 1))" "${options[$i]}"
    done

    read -r -p "Select [${default_index}]: " choice
    choice="${choice:-${default_index}}"

    if ! [[ "${choice}" =~ ^[0-9]+$ ]] || (( choice < 1 || choice > ${#options[@]} )); then
        echo "Invalid selection: ${choice}"
        exit 1
    fi

    MENU_CHOICE_INDEX="${choice}"
    MENU_CHOICE_LABEL="${options[$((choice - 1))]}"
}

prompt_custom() {
    local prompt="$1"
    local value
    read -r -p "${prompt}: " value
    if [[ -z "${value}" ]]; then
        echo "Value required."
        exit 1
    fi
    printf '%s' "${value}"
}

guild_default="${DISCORD_SERVER_ID:-668903786361651200}"

echo "Discord export wizard"
echo "Using config: ${ENV_FILE}"
echo
echo "Configured guild ID: ${guild_default}"
read -r -p "Press Enter to use this guild, or type another guild ID: " guild_input
guild_id="${guild_input:-${guild_default}}"

channel_options=(
    "development | 669989266478202917"
    "dev-support | 840313005064585246"
    "ergoscript-support | 849659724495323206"
    "support | 670288337747312646"
    "ask-anything | 908347206988365864"
    "mining | 668913770059268125"
    "dev-tooling | 1073483623459725322"
    "rosen | 964131671609860126"
    "sigmausd | 802828538197573682"
    "custom channel ID"
)
choose_menu "Channel" 1 "${channel_options[@]}"
channel_label="${MENU_CHOICE_LABEL}"
if [[ "${channel_label}" == "custom channel ID" ]]; then
    channel_name="custom"
    channel_id="$(prompt_custom "Channel ID")"
else
    channel_name="${channel_label%% | *}"
    channel_id="${channel_label##* | }"
fi

timeframe_options=(
    "1 week"
    "1 month"
    "since start of year"
    "1 year"
    "all time"
)
choose_menu "Timeframe" 1 "${timeframe_options[@]}"
timeframe="${MENU_CHOICE_LABEL}"

after_date=""
timeframe_slug="$(slugify "${timeframe}")"
case "${timeframe}" in
    "1 week")
        after_date="$(days_ago 7)"
        ;;
    "1 month")
        after_date="$(one_month_ago)"
        ;;
    "since start of year")
        after_date="$(start_of_year)"
        ;;
    "1 year")
        after_date="$(days_ago 365)"
        ;;
    "all time")
        after_date=""
        ;;
esac

format_options=("Json" "PlainText" "Html" "Csv")
choose_menu "Export format" 1 "${format_options[@]}"
export_format="${MENU_CHOICE_LABEL}"

export_date="$(date_utc '+%Y-%m-%d')"
timestamp="$(date_utc '+%H%M%S')"
channel_slug="$(slugify "${channel_name}")"
format_slug="$(slugify "${export_format}")"
guild_slug="$(slugify "${guild_id}")"
output_dir="output/${export_date}/manual-export"

output_path="${output_dir}/guild-${guild_slug}-${channel_slug}-${channel_id}-${timeframe_slug}-${timestamp}.${format_slug}"

echo
echo "Export plan"
echo "  Guild:     ${guild_id}"
echo "  Channel:   ${channel_name} (${channel_id})"
echo "  Timeframe: ${timeframe}"
echo "  Format:    ${export_format}"
echo "  Output:    ${output_path}"
echo
read -r -p "Run export? [Y/n]: " confirm
confirm="${confirm:-Y}"
if [[ ! "${confirm}" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

mkdir -p "${output_dir}"

export_command=(
    "${EXPORTER}" export
    --channel "${channel_id}"
    --token "${DISCORD_TOKEN}"
)
if [[ -n "${after_date}" ]]; then
    export_command+=(--after "${after_date}")
fi
export_command+=(
    --format "${export_format}"
    -o "${output_path}"
)

"${export_command[@]}"

echo
echo "Exported file:"
echo "${output_path}"
