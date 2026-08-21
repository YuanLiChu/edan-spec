#!/usr/bin/env bash
# EdanSpec Setup Script
# 将 EdanSpec 规范资产（单一规范源）按平台部署到目标项目目录。
#   规范文档只维护一份 AGENTS.md，claudecode 部署时派生为 CLAUDE.md。
#   claudecode → {target}/.claude/   （AGENTS.md 派生为 CLAUDE.md + docs + rules + skills）
#   opencode   → {target}/.opencode/ （AGENTS.md + docs + rules + skills）+ {target}/opencode.json
#   Windows 请使用 setup.bat（功能对等，cmd.exe / PowerShell 直接运行，无需 bash/python）。
# Usage: ./setup.sh <target-dir> <platform>
#   platform: claudecode | opencode

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
    cat <<EOF
Usage: ./setup.sh <target-dir> <platform>

Arguments:
  target-dir   Target project directory (will be created if not exists)
  platform     claudecode — 部署到 {target}/.claude/
               opencode   — 部署到 {target}/.opencode/ + {target}/opencode.json

EdanSpec 采用单一规范源：仓库根目录只维护一份 AGENTS.md，setup.sh 按平台展开部署：
  claudecode: AGENTS.md（重命名为 CLAUDE.md）/ docs / rules / skills → {target}/.claude/
  opencode:   AGENTS.md / docs / rules / skills → {target}/.opencode/，并生成 opencode.json

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

# Source directory: single source of truth at repo root
SRC_DIR="$SCRIPT_DIR"

# Validate source assets exist per platform
if [ "$PLATFORM" = "claudecode" ]; then
    ASSETS="AGENTS.md docs rules skills"
else
    ASSETS="AGENTS.md docs rules skills opencode.json"
fi
for asset in $ASSETS; do
    if [ ! -e "$SRC_DIR/$asset" ]; then
        echo "ERROR: Source asset '$SRC_DIR/$asset' not found."
        exit 1
    fi
done

# Create target directory if needed
mkdir -p "$TARGET_DIR"

echo "============================================"
echo "  EdanSpec Setup"
echo "  Platform: $PLATFORM"
echo "  Source:   $SRC_DIR"
echo "  Target:   $TARGET_DIR"
echo "============================================"

# Copy a single file to dest (rename allowed), excluding .DS_Store
copy_file_as() {
    local src="$1"
    local dst="$2"
    if command -v rsync &>/dev/null; then
        rsync -a --exclude='.DS_Store' "$src" "$dst"
    else
        cp "$src" "$dst"
    fi
}

# Copy given items into dest keeping original names, excluding .DS_Store
copy_items() {
    local dest="$1"
    shift
    if command -v rsync &>/dev/null; then
        local item
        for item in "$@"; do
            rsync -a --exclude='.DS_Store' "$SRC_DIR/$item" "$dest/"
        done
    else
        local item
        for item in "$@"; do
            cp -r "$SRC_DIR/$item" "$dest/"
        done
        find "$dest" -name '.DS_Store' -type f -delete 2>/dev/null || true
    fi
}

# Generate deployment opencode.json with instructions pointing into .opencode/
generate_opencode_json() {
    python3 - "$SRC_DIR/opencode.json" "$TARGET_DIR/opencode.json" <<'PY'
import json
import sys

src, dst = sys.argv[1], sys.argv[2]
cfg = json.load(open(src, encoding="utf-8"))
cfg["instructions"] = [
    ".opencode/AGENTS.md",
    ".opencode/docs/**/*.md",
    ".opencode/rules/**/*.md",
]
with open(dst, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
    f.write("\n")
PY
}

if [ "$PLATFORM" = "claudecode" ]; then
    DEST="$TARGET_DIR/.claude"
    mkdir -p "$DEST"
    copy_file_as "$SRC_DIR/AGENTS.md" "$DEST/CLAUDE.md"
    copy_items "$DEST" docs rules skills
    echo "Copied to $DEST (AGENTS.md -> CLAUDE.md)"
else
    DEST="$TARGET_DIR/.opencode"
    mkdir -p "$DEST"
    copy_items "$DEST" AGENTS.md docs rules skills
    echo "Copied to $DEST"
    generate_opencode_json
    echo "Generated $TARGET_DIR/opencode.json"
fi

echo ""
echo "Done! EdanSpec resources have been set up for $PLATFORM."
echo ""
if [ "$PLATFORM" = "claudecode" ]; then
    echo "Next steps:"
    echo "  cd $TARGET_DIR"
    echo "  claude                  # Start Claude Code"
    echo "  /skills                 # Verify skills are loaded"
else
    echo "Next steps:"
    echo "  cd $TARGET_DIR"
    echo "  opencode                # Start OpenCode"
    echo "  Verify skills are loaded in the session"
fi
