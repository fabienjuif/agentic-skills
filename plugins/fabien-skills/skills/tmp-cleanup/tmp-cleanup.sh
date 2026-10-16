#!/usr/bin/env bash
# Clean stale top-level entries from a temp dir. Linux and macOS (bash 3.2 compatible).
# Dry-run by default; pass --apply to delete.
#   --hours N   age threshold in hours (default 3)
#   --dir PATH  directory to clean (default /tmp on Linux, $TMPDIR on macOS)
# Env: TMP_CLEANUP_KEEP="pat1 pat2" adds extra name globs to protect.
set -euo pipefail

os=$(uname -s)
hours=3
apply=0
if [ "$os" = Darwin ]; then dir=${TMPDIR:-/tmp}; else dir=/tmp; fi
while [ $# -gt 0 ]; do
  case $1 in
    --apply) apply=1 ;;
    --hours) hours=$2; shift ;;
    --dir) dir=$2; shift ;;
    *) echo "usage: $0 [--apply] [--hours N] [--dir PATH]" >&2; exit 2 ;;
  esac
  shift
done

# Live state: X/Qt/lock files, multiplexer sockets, systemd/ssh, macOS system temp, and
# the session dirs of the agents themselves (Claude Code scratchpad, Codex daemon/sandbox).
keep=(
  '.X*' '.ICE-unix' '.font-unix' '.XIM-unix' '.Test-unix'
  'claude-*' 'cc-daemon-*' 'codex-*' 'tmux-*' 'zellij-*' 'qtsingleapp*' '*.lock'
  'systemd-private-*' 'ssh-*' 'com.apple.*' 'TemporaryItems'
)
# shellcheck disable=SC2206
keep+=(${TMP_CLEANUP_KEEP:-})
prune=()
for k in "${keep[@]}"; do prune+=(! -name "$k"); done

# macOS has no tmpfs temp dir, so deleting there never frees RAM.
if [ "$os" = Linux ]; then
  fstype=$(df --output=fstype "$dir" | tail -1 | tr -d ' ')
else
  fstype=disk
fi
[ "$fstype" = tmpfs ] || echo "note: $dir is on $fstype, not tmpfs; deleting here won't free RAM"

echo "before:"; df -h "$dir" | tail -1
victims=()
while IFS= read -r -d '' f; do
  victims+=("$f")
done < <(find "$dir" -mindepth 1 -maxdepth 1 -user "$(id -un)" -mmin +$((hours * 60)) \
  "${prune[@]}" -print0)
echo "${#victims[@]} entries older than ${hours}h"

if [ "$apply" -eq 0 ]; then
  if [ "${#victims[@]}" -gt 0 ]; then
    du -sk "${victims[@]}" 2>/dev/null | awk '{s+=$1} END {printf "%.1f MiB\n", s/1024}'
  fi
  echo "dry run, pass --apply to delete"
  exit 0
fi

if [ "${#victims[@]}" -gt 0 ]; then rm -rf -- "${victims[@]}"; fi
echo "after:"; df -h "$dir" | tail -1
