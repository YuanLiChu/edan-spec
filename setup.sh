#!/usr/bin/env bash
# EdanSpec Setup Script
# Copies EdanSpec agent resources to a target project directory.
# Usage: ./setup.sh <target-dir> <platform>
#   platform: claudecode | opencode

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
    cat <<EOF
Usage: ./setup.sh <target-dir> <platform>

Arguments:
  target-dir   Target project directory (will be created if not exists)
  platform     Target agent platform:
               claudecode  — Copy .claude/ to target (Claude Code)
               opencode    — Copy .opencode/ + opencode.json to target (OpenCode)

Examples:
  ./setup.sh /path/to/my-project claudecode
  ./setup.sh /path/to/my-project opencode
EOF
    exit 1
}

# Argument validation
if [ $# -lt 2 ]; then
    usage
fi

TARGET_DIR="$1"
PLATFORM="$2"

# Platform validation
if [ "$PLATFORM" != "claudecode" ] && [ "$PLATFORM" != "opencode" ]; then
    echo "ERROR: Unknown platform '$PLATFORM'. Must be 'claudecode' or 'opencode'."
    usage
fi

# Source directory validation
if [ "$PLATFORM" = "claudecode" ]; then
    SRC_DIR="$SCRIPT_DIR/claudecode"
    if [ ! -d "$SRC_DIR/.claude" ]; then
        echo "ERROR: Source directory '$SRC_DIR/.claude' not found."
        exit 1
    fi
elif [ "$PLATFORM" = "opencode" ]; then
    SRC_DIR="$SCRIPT_DIR/opencode"
    if [ ! -d "$SRC_DIR/.opencode" ] || [ ! -f "$SRC_DIR/opencode.json" ]; then
        echo "ERROR: Source files in '$SRC_DIR' not found."
        exit 1
    fi
fi

# Create target directory if needed
mkdir -p "$TARGET_DIR"

echo "============================================"
echo "  EdanSpec Setup"
echo "  Platform: $PLATFORM"
echo "  Source:   $SCRIPT_DIR"
echo "  Target:   $TARGET_DIR"
echo "============================================"

# Perform copy (exclude .DS_Store files)
# Using rsync if available, otherwise cp + find cleanup
if command -v rsync &>/dev/null; then
    if [ "$PLATFORM" = "claudecode" ]; then
        rsync -a --exclude='.DS_Store' "$SRC_DIR/" "$TARGET_DIR/"
        echo "Copied .claude/ to $TARGET_DIR"
    elif [ "$PLATFORM" = "opencode" ]; then
        rsync -a --exclude='.DS_Store' "$SRC_DIR/" "$TARGET_DIR/"
        echo "Copied .opencode/ and opencode.json to $TARGET_DIR"
    fi
else
    # Fallback: use cp then clean up .DS_Store
    if [ "$PLATFORM" = "claudecode" ]; then
        cp -r "$SRC_DIR/." "$TARGET_DIR/"
    elif [ "$PLATFORM" = "opencode" ]; then
        cp -r "$SRC_DIR/." "$TARGET_DIR/"
    fi
    # Clean up macOS metadata files
    find "$TARGET_DIR" -name '.DS_Store' -type f -delete 2>/dev/null || true
fi

echo ""
echo "Done! EdanSpec resources have been set up for $PLATFORM."
echo ""
if [ "$PLATFORM" = "claudecode" ]; then
    echo "Next steps:"
    echo "  cd $TARGET_DIR"
    echo "  claude                  # Start Claude Code"
    echo "  /skills                 # Verify skills are loaded"
elif [ "$PLATFORM" = "opencode" ]; then
    echo "Next steps:"
    echo "  cd $TARGET_DIR"
    echo "  opencode                # Start OpenCode"
    echo "  Verify agents and skills are loaded in the session"
fi
