#!/usr/bin/env bash
# Owl alpha installer.
#
#   install (default)   put Owl into a folder, or update it there. Never touches data/ inside it.
#   uninstall           remove Owl's program files. Keeps data/ unless --delete-data is given.
#
# Options: --target DIR   the Owl folder. Default: ~/Owl. Use --target "$PWD" for the current folder.
#          --intake FILE  notes to hand to Owl before the first conversation
#          --delete-data  with uninstall: also remove the personal data folder
#
# Piped use: curl -fsSL https://raw.githubusercontent.com/LeeAao/owl-alpha/main/install.sh | bash -s -- --target "$PWD"
#            ... | bash -s -- uninstall --target "$PWD"

set -u

REPO="LeeAao/owl-alpha"
BRANCH="main"
TARGET="${OWL_DIR:-$HOME/Owl}"
CMD="install"
INTAKE=""
DELETE_DATA=0
MARKER=".owl-version"
# Everything the installer owns inside TARGET. data/ is deliberately not in this list.
MANAGED=".claude/skills/owl .agents/skills/owl tools CLAUDE.md AGENTS.md OWL-README.md $MARKER"

say()  { printf '%s\n' "$*"; }
fail() { printf 'Owl install stopped: %s\n' "$*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    install|uninstall) CMD="$1" ;;
    --target) [ $# -ge 2 ] || fail "--target needs a folder"; TARGET="$2"; shift ;;
    --intake) [ $# -ge 2 ] || fail "--intake needs a file"; INTAKE="$2"; shift ;;
    --delete-data) DELETE_DATA=1 ;;
    -h|--help) sed -n '2,13p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) fail "unknown argument: $1" ;;
  esac
  shift
done

# A folder is ours if it carries the marker. A folder holding nothing but data/ is what an
# uninstall leaves behind, so it counts as ours too.
is_owl_dir() { [ -f "$TARGET/$MARKER" ] || [ "$(ls -A "$TARGET" 2>/dev/null)" = "data" ]; }
# In a folder that isn't ours yet, the first thing Owl would overwrite. Empty if nothing.
first_conflict() {
  for item in $MANAGED data; do
    [ -e "$TARGET/$item" ] && { printf '%s' "$item"; return; }
  done
}

# Work with a full path, so messages are unambiguous and "." can't be mistaken for the home folder.
[ -d "$TARGET" ] && TARGET="$(cd "$TARGET" && pwd)"

if [ "$CMD" = "uninstall" ]; then
  [ -d "$TARGET" ] || { say "Nothing to remove: $TARGET does not exist."; exit 0; }
  is_owl_dir || fail "$TARGET is not an Owl install (no $MARKER inside). Nothing was removed."
  for item in $MANAGED; do
    rm -rf "${TARGET:?}/$item"
  done
  rmdir "$TARGET/.claude/skills" "$TARGET/.claude" "$TARGET/.agents/skills" "$TARGET/.agents" 2>/dev/null
  if [ "$DELETE_DATA" -eq 1 ]; then
    rm -rf "${TARGET:?}/data"
    rmdir "$TARGET" 2>/dev/null
    say "Owl removed from $TARGET, including personal data."
  elif [ -d "$TARGET/data" ] && [ -n "$(ls -A "$TARGET/data" 2>/dev/null)" ]; then
    say "Owl removed. Your personal data is still in $TARGET/data."
    say "To delete it too, run uninstall again with --delete-data."
  else
    rmdir "$TARGET/data" "$TARGET" 2>/dev/null
    say "Owl removed from $TARGET."
  fi
  exit 0
fi

# ---- install / update ----

HOME_DIR="$(cd "$HOME" 2>/dev/null && pwd)"
if [ "$TARGET" = "$HOME_DIR" ] || [ "$TARGET" = "/" ]; then
  fail "Owl needs a folder of its own, and $TARGET is not one. Make a new folder (for example Owl) and install there."
fi
if ! is_owl_dir; then
  CONFLICT="$(first_conflict)"
  [ -z "$CONFLICT" ] || fail "$TARGET already contains '$CONFLICT', which Owl would overwrite. Use a new, empty folder."
fi

# Python 3.9+ is the only requirement. Check before changing anything.
PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
    PY="$candidate"
    break
  fi
done
if [ -z "$PY" ]; then
  say "Owl needs Python 3.9 or newer, and this computer doesn't have it yet."
  say "On a Mac: run   xcode-select --install   , finish the popup, then run this installer again."
  exit 1
fi

# Source: the folder this script sits in (a clone), otherwise a fresh download.
SRC=""
CLEANUP=""
SELF="${BASH_SOURCE[0]:-}"
if [ -n "$SELF" ] && [ -f "$(dirname "$SELF")/skill/SKILL.md" ]; then
  SRC="$(cd "$(dirname "$SELF")" && pwd)"
else
  command -v curl >/dev/null 2>&1 || fail "curl is missing."
  command -v tar  >/dev/null 2>&1 || fail "tar is missing."
  CLEANUP="$(mktemp -d)" || fail "could not create a temporary folder."
  trap 'rm -rf "$CLEANUP"' EXIT
  curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH" | tar -xz -C "$CLEANUP" \
    || fail "could not download Owl from github.com/$REPO. Check the internet connection and try again."
  SRC="$(find "$CLEANUP" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  [ -f "$SRC/skill/SKILL.md" ] || fail "the download looks incomplete."
fi

WAS_INSTALLED=0
is_owl_dir && WAS_INSTALLED=1

mkdir -p "$TARGET/.claude/skills" "$TARGET/.agents/skills" "$TARGET/data" || fail "cannot write to $TARGET."
chmod 700 "$TARGET/data" 2>/dev/null
TARGET="$(cd "$TARGET" && pwd)"

# Replace program files wholesale so removed files don't linger after an update.
rm -rf "$TARGET/.claude/skills/owl" "$TARGET/.agents/skills/owl" "$TARGET/tools"
cp -R "$SRC/skill" "$TARGET/.claude/skills/owl" || fail "copy failed."
cp -R "$SRC/skill" "$TARGET/.agents/skills/owl" || fail "copy failed."
cp -R "$SRC/tools" "$TARGET/tools"              || fail "copy failed."
cp "$SRC/templates/CLAUDE.md" "$TARGET/CLAUDE.md" || fail "copy failed."
cp "$SRC/templates/AGENTS.md" "$TARGET/AGENTS.md" || fail "copy failed."
cp "$SRC/README.md" "$TARGET/OWL-README.md"       || fail "copy failed."
cp "$SRC/VERSION" "$TARGET/$MARKER"               || fail "copy failed."

# Intake notes: an explicit file wins, then an intake*.md lying in the Owl folder itself (it is
# moved into data/), then the newest intake*.md in Downloads. Never overwrite one already in place.
INTAKE_NOTE="none found. That's fine: Owl will just ask a few more questions."
if [ -f "$TARGET/data/intake.md" ]; then
  INTAKE_NOTE="already in place."
else
  MOVE=0
  if [ -n "$INTAKE" ]; then
    [ -f "$INTAKE" ] || fail "intake file not found: $INTAKE"
  else
    INTAKE="$(ls -t "$TARGET"/intake*.md 2>/dev/null | head -n 1)"
    if [ -n "$INTAKE" ]; then
      MOVE=1
    else
      INTAKE="$(ls -t "$HOME"/Downloads/intake*.md 2>/dev/null | head -n 1)"
    fi
  fi
  if [ -n "$INTAKE" ] && [ -f "$INTAKE" ]; then
    if [ "$MOVE" -eq 1 ]; then
      mv "$INTAKE" "$TARGET/data/intake.md" && INTAKE_NOTE="found in the folder and moved to data/intake.md"
    else
      cp "$INTAKE" "$TARGET/data/intake.md" && INTAKE_NOTE="copied from $INTAKE"
    fi
    chmod 600 "$TARGET/data/intake.md" 2>/dev/null
  fi
fi

VERSION="$(cat "$TARGET/$MARKER")"
say ""
if [ "$WAS_INSTALLED" -eq 1 ]; then
  say "Owl updated to $VERSION. Your data in $TARGET/data was not touched."
else
  say "Owl $VERSION is installed in $TARGET"
fi
say "Intake notes: $INTAKE_NOTE"
say ""
say "Next: in a Claude or Codex session opened in $TARGET, say hi."
say ""
say "If you are an AI agent that just ran this for someone: Owl is the skill at"
say "  $TARGET/.claude/skills/owl/SKILL.md"
say "Read that file now and continue as Owl in this same conversation, starting with its first step."
say "Don't summarize the installation and don't ask whether to start. The person is waiting for Owl to say hello."
if [ -z "$CLEANUP" ] && [ "${SRC#"$TARGET"/}" != "$SRC" ]; then
  say "The downloaded copy in $SRC is no longer needed. Leave it there and don't ask the person to delete it."
fi
