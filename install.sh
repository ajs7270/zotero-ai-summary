#!/usr/bin/env bash
# AI Summary for Zotero installer — Zotero plugin + summary/pinpoint-lesson skills
# for Claude Code, OpenAI Codex CLI, and Google Gemini CLI.
#
# Usage:
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/ajs7270/zotero-ai-summary/main/install.sh)"
#
# Or after cloning the repo locally:
#   bash install.sh
#
# Environment overrides:
#   AI_SUMMARY_REPO              GitHub slug (default: ajs7270/zotero-ai-summary)
#   AI_SUMMARY_REF               Branch/tag (default: main)
#   AI_SUMMARY_LOCAL             Path to a local checkout (skips network download)
#   AI_SUMMARY_CLIS              Space-separated list (claude codex gemini), bypasses prompt
#   AI_SUMMARY_SKILLS            Comma-separated list (summary,pinpoint-lesson), default both
#   AI_SUMMARY_SKIP_PLUGIN       Set to 1 to skip Zotero plugin install
#   AI_SUMMARY_SKIP_DEPS_CHECK   Set to 1 to skip Poppler / Python check
set -euo pipefail

REPO="${AI_SUMMARY_REPO:-ajs7270/zotero-ai-summary}"
REF="${AI_SUMMARY_REF:-main}"
LOCAL_DIR="${AI_SUMMARY_LOCAL:-}"
SKIP_PLUGIN="${AI_SUMMARY_SKIP_PLUGIN:-0}"
SKIP_DEPS="${AI_SUMMARY_SKIP_DEPS_CHECK:-0}"
SKILLS_RAW="${AI_SUMMARY_SKILLS:-summary,pinpoint-lesson}"

bold() { printf '\033[1m%s\033[0m\n' "$*" >&2; }
ok()   { printf '\033[32m✓\033[0m %s\n' "$*" >&2; }
warn() { printf '\033[33m!\033[0m %s\n' "$*" >&2; }
err()  { printf '\033[31m✗\033[0m %s\n' "$*" >&2; }

prompt_yes_no() {
  local question="$1" default="${2:-y}" reply
  read -r -p "$question [$default] " reply || true
  reply="${reply:-$default}"
  [[ "$reply" =~ ^[Yy]$ ]]
}

choose_clis() {
  if [[ -n "${AI_SUMMARY_CLIS:-}" ]]; then
    printf '%s' "$AI_SUMMARY_CLIS"
    return
  fi
  bold "Which AI CLIs do you want to install the skills into?"
  echo "  1) Claude Code       (~/.claude/skills/<skill>/)" >&2
  echo "  2) OpenAI Codex CLI  (~/.codex/skills/<skill>/)" >&2
  echo "  3) Google Gemini CLI (~/.gemini/skills/<skill>/)" >&2
  echo "  a) All of the above" >&2
  echo "  s) Skip skill install" >&2
  read -r -p "Enter choices separated by spaces (e.g. '1 2'), or 'a' / 's' [a]: " reply || true
  reply="${reply:-a}"
  case "$reply" in
    s|S)      printf '' ;;
    a|A|all)  printf 'claude codex gemini' ;;
    *)
      local out=()
      for c in $reply; do
        case "$c" in
          1) out+=("claude") ;;
          2) out+=("codex") ;;
          3) out+=("gemini") ;;
          claude|codex|gemini) out+=("$c") ;;
        esac
      done
      printf '%s' "${out[*]}"
      ;;
  esac
}

split_skills() {
  # Split on commas, trim spaces inside each entry, drop empty entries.
  printf '%s' "$1" | awk -v RS=',' '{ gsub(/[[:space:]]/, ""); if (length($0) > 0) print }'
}

skill_dir_for() {
  local cli="$1" skill="$2"
  case "$cli" in
    claude) echo "$HOME/.claude/skills/$skill" ;;
    codex)  echo "$HOME/.codex/skills/$skill" ;;
    gemini) echo "$HOME/.gemini/skills/$skill" ;;
    *)      err "Unknown CLI: $cli"; return 1 ;;
  esac
}

ensure_workdir() {
  if [[ -n "$LOCAL_DIR" ]]; then
    SOURCE_DIR="$LOCAL_DIR"
    ok "Using local checkout at $SOURCE_DIR"
    return
  fi
  SOURCE_DIR="$(mktemp -d)"
  trap 'rm -rf "$SOURCE_DIR"' EXIT
  bold "Downloading AI Summary for Zotero $REF from $REPO ..."
  curl -fsSL "https://github.com/$REPO/archive/refs/heads/$REF.tar.gz" \
    | tar -xz -C "$SOURCE_DIR" --strip-components=1
  ok "Downloaded into $SOURCE_DIR"
}

install_skill_for() {
  local cli="$1" skill="$2" target
  local source_path="$SOURCE_DIR/skill/$skill"
  if [[ ! -d "$source_path" ]]; then
    err "Skill source missing at $source_path"
    return 1
  fi
  target="$(skill_dir_for "$cli" "$skill")"
  mkdir -p "$(dirname "$target")"
  rm -rf "$target"
  cp -R "$source_path" "$target"
  ok "Installed skill '$skill' into $target ($cli)"
}

install_plugin() {
  if [[ "$SKIP_PLUGIN" == "1" ]]; then
    warn "Skipping Zotero plugin install (AI_SUMMARY_SKIP_PLUGIN=1)."
    return
  fi
  if ! prompt_yes_no "Install the Zotero plugin (.xpi) now?" "y"; then
    warn "Skipped Zotero plugin install."
    return
  fi
  local xpi=""
  if compgen -G "$SOURCE_DIR/dist/zotero-ai-summary-*.xpi" >/dev/null; then
    xpi="$(ls -t "$SOURCE_DIR"/dist/zotero-ai-summary-*.xpi | head -1)"
  else
    bold "Downloading the latest plugin release ..."
    xpi="$(mktemp -t ai-summary).xpi"
    curl -fsSL "https://github.com/$REPO/releases/latest/download/zotero-ai-summary.xpi" -o "$xpi" \
      || { err "Could not download zotero-ai-summary.xpi from $REPO releases"; return 1; }
  fi
  ok "Plugin xpi ready at: $xpi"
  # Zotero 9 only accepts plugin installs through Tools → Plugins → Install Plugin From File.
  # `open -a Zotero <file>.xpi` is treated as a regular file import, not a plugin install,
  # and Zotero exposes no `-install-extension` CLI flag (the Mozilla flag was removed
  # years ago). Profile-side injection (extensions/<id>.xpi) lands the file in the
  # profile but Zotero parks it as inactive without prompting. The reliable path is
  # to bring Zotero forward and reveal the xpi in Finder so the user finishes the
  # install through the Plugins manager.
  if [[ "$(uname)" == "Darwin" ]] && command -v osascript >/dev/null 2>&1; then
    osascript -e 'tell application "Zotero" to activate' >/dev/null 2>&1 || true
    if command -v open >/dev/null 2>&1; then
      open -R "$xpi" 2>/dev/null || true
    fi
  fi
  cat >&2 <<HOWTO

To finish the plugin install in Zotero:
  1. Switch to Zotero (it has been brought to the foreground if available).
  2. Open Tools -> Plugins.
  3. Click the gear icon (top right) -> Install Plugin From File...
  4. Select the xpi:
       $xpi
     (already revealed in Finder on macOS).
  5. Click Install. No restart required.
HOWTO
}

check_deps() {
  if [[ "$SKIP_DEPS" == "1" ]]; then return; fi
  bold "Checking optional dependencies ..."
  local missing=()
  for cmd in pdftotext pdfimages pdftoppm; do
    if command -v "$cmd" >/dev/null 2>&1; then
      ok "$cmd found"
    else
      missing+=("$cmd")
    fi
  done
  if command -v python3 >/dev/null 2>&1; then
    ok "python3 found ($(python3 --version))"
  else
    missing+=("python3")
  fi
  if [[ ${#missing[@]} -gt 0 ]]; then
    warn "Missing: ${missing[*]}"
    cat >&2 <<HINT

Install hints:
  macOS    : brew install poppler && brew install python
  Ubuntu   : sudo apt install poppler-utils python3
  Arch     : sudo pacman -S poppler python
HINT
  fi
}

print_done() {
  cat >&2 <<DONE

$(bold "AI Summary for Zotero installation complete.")

Next steps:
  1. Open Zotero (9.0+) and confirm AI Summary for Zotero is listed under Tools -> Plugins.
  2. Verify the plugin is alive:
       curl http://localhost:23119/aisummary/health
  3. In your AI CLI, invoke either skill:
       /summary <path-to-paper.pdf>           - quick structured summary
       /pinpoint-lesson <path-to-paper.pdf>   - long-form pin-point lesson

Docs:
  https://github.com/$REPO
DONE
}

main() {
  bold "AI Summary for Zotero installer"
  ensure_workdir

  CLIS_RAW="$(choose_clis)"
  if [[ -z "$CLIS_RAW" ]]; then
    warn "No CLI selected - skill install skipped."
  else
    SKILLS=()
    while IFS= read -r s; do SKILLS+=("$s"); done < <(split_skills "$SKILLS_RAW")
    if [[ ${#SKILLS[@]} -eq 0 ]]; then
      warn "AI_SUMMARY_SKILLS is empty - no skills will be installed."
    else
      for cli in $CLIS_RAW; do
        for skill in "${SKILLS[@]}"; do
          install_skill_for "$cli" "$skill"
        done
      done
    fi
  fi

  install_plugin
  check_deps
  print_done
}

main "$@"
