# Sourced by the other scripts. Sets forge (github | forgejo) from origin, and
# for Forgejo api, token and fj (an authenticated curl), since gh cannot see
# it. A host gh is logged in to is GitHub (github.com or Enterprise); any other
# is Forgejo/Gitea. Probing /api/v1/version was tried: instances that require
# sign-in answer it 403.
read -r host repo < <(python3 -c '
import re, sys
m = re.match(r"^(?:[a-z+]+://)?(?:[^@/]+@)?([^:/]+)(?::\d+)?[:/](.+?)(?:\.git)?/?$", sys.argv[1])
print(m[1], m[2])' "$(git remote get-url origin)")
forge=github
if [ "$host" != github.com ] && ! gh auth status --hostname "$host" >/dev/null 2>&1; then
    forge=forgejo
    api=https://$host/api/v1/repos/$repo
    token=${FORGEJO_TOKEN:-}
    [ -n "$token" ] || token=$(sed -n 's/^FORGEJO_TOKEN=//p' ~/.claude/.env 2>/dev/null | tail -1 || true)
    [ -n "$token" ] || token=$(printf 'protocol=https\nhost=%s\n\n' "$host" |
        GIT_TERMINAL_PROMPT=0 git credential fill 2>/dev/null | sed -n 's/^password=//p')
    [ -n "$token" ] || { echo "no Forgejo token for $host: set FORGEJO_TOKEN" >&2; exit 1; }
    fj() { curl -s -H "Authorization: token $token" "$@"; }
fi
