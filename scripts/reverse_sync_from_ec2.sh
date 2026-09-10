#!/bin/bash
# Reverse-sync EC2 → local for EC2-deployed repos. EC2 is where code is developed,
# built and tested; local git is only the commit surface. Run this BEFORE any local
# commit or push (rule restated by Donny 2026-09-10).
#
# Default mode: DRY-RUN. Pass --apply to pull.
# Pull policy: --update (only files that are newer on EC2, or exist only on EC2) with
# checksum comparison. Files where LOCAL is newer are never overwritten; they are listed
# under "pending forward deploy" so you can rsync them up (additively, never --delete).
#
# Usage:
#   scripts/reverse_sync_from_ec2.sh                 # dry-run, all repos
#   scripts/reverse_sync_from_ec2.sh --apply          # pull EC2 → local
#   scripts/reverse_sync_from_ec2.sh --repo datapai-platform-be [--apply]
#
# Per-repo extra excludes: scripts/reverse_sync_excludes/<repo>.txt (rsync --exclude-from),
# e.g. datapai-stock-be scripts that were copied into platform-be on EC2 by hand.

set -u

EC2="ec2-user@platform.datap.ai"
KEY="$HOME/.ssh/Linux-CodeCambat.pem"
SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no"
HERE="$(cd "$(dirname "$0")" && pwd)"

EXCLUDES=(
    --exclude .git --exclude __pycache__ --exclude "*.pyc" --exclude node_modules --exclude .next
    --exclude target --exclude dbt_packages --exclude logs --exclude ".env*" --exclude out
    --exclude .venv --exclude venv --exclude .pytest_cache --exclude .DS_Store --exclude .claude
    --exclude .gstack --exclude "*.bak*" --exclude "*.duckdb" --exclude "*.sqlite"
)

# Repos deployed by rsync (no usable .git on EC2). datapai-platform-be on EC2 is NOT a git
# checkout (verified 2026-09-09) — it belongs here, not in a git-bundle flow.
REPOS=(
    datapai-platform-be
    datapai-ai-etl
    datapai-stock-be
    datapai-platform-menu
    datapai-dbt-governance
    dbt-demo
)

APPLY=0; ONLY=""; ALLOW_DIRTY=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --apply) APPLY=1 ;;
        --repo) ONLY="$2"; shift ;;
        --allow-dirty) ALLOW_DIRTY=1 ;;   # pull even with uncommitted local changes (the --update rule still protects newer local files)
        *) echo "unknown arg $1" >&2; exit 2 ;;
    esac
    shift
done

echo "EC2 reverse-sync — mode: $([[ $APPLY -eq 1 ]] && echo APPLY || echo dry-run)"
echo "───────────────────────────────────────────────────────────"

for repo in "${REPOS[@]}"; do
    [[ -n "$ONLY" && "$repo" != "$ONLY" ]] && continue
    local_dir="$HOME/git/$repo"
    remote_dir="/home/ec2-user/git/$repo/"
    [[ ! -d "$local_dir" ]] && { echo "⚠  $repo — local dir missing, skipped"; continue; }
    extra=()
    [[ -f "$HERE/reverse_sync_excludes/$repo.txt" ]] && extra=(--exclude-from "$HERE/reverse_sync_excludes/$repo.txt")

    # Safety: refuse --apply on a dirty working tree (an in-flight local edit would be clobbered).
    if [[ $APPLY -eq 1 && $ALLOW_DIRTY -eq 0 && -d "$local_dir/.git" ]]; then
        if ! git -C "$local_dir" diff --quiet || ! git -C "$local_dir" diff --cached --quiet; then
            echo "▶ $repo — ABORT: uncommitted local changes; commit or set them aside first." >&2
            continue
        fi
    fi

    echo "▶ $repo  (EC2 → local, only EC2-newer / EC2-only files)"
    flags=(-rtcz --update --itemize-changes); [[ $APPLY -eq 0 ]] && flags+=(--dry-run)
    rsync "${flags[@]}" "${EXCLUDES[@]}" "${extra[@]}" -e "ssh $SSH_OPTS" "$EC2:$remote_dir" "$local_dir/" 2>/dev/null \
        | grep -E "^>f" | awk '{print "    pull  " $2}'
    echo "  pending forward deploy (LOCAL newer than EC2 — not touched):"
    rsync -rtcn --update --itemize-changes "${EXCLUDES[@]}" "${extra[@]}" -e "ssh $SSH_OPTS" "$local_dir/" "$EC2:$remote_dir" 2>/dev/null \
        | grep -E "^<f" | awk '{print "    local " $2}' | head -30
    echo
done

echo "───────────────────────────────────────────────────────────"
echo "Next: review \`git status\` in each repo, commit the pulled hotfixes, then push (with confirmation)."
echo "Forward deploy of local-newer files: rsync -avz (NO --delete) local → EC2, then test on EC2."
