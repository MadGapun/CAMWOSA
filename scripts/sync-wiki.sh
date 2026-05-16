#!/usr/bin/env bash
#
# sync-wiki.sh — Spiegelt docs/wiki/ ins GitHub-Wiki.
#
# Voraussetzungen:
# - Wiki-Repo ist als Geschwister-Verzeichnis zu CAMWOSA geklont:
#     git clone https://github.com/MadGapun/CAMWOSA.wiki.git CAMWOSA-wiki
# - bash + sed verfuegbar (Git-Bash unter Windows funktioniert)
#
# Nutzung:
#   bash scripts/sync-wiki.sh [--dry-run]
#
# Siehe Issue #15 (Living Wiki-Issue).

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WIKI_DIR="${WIKI_DIR:-$REPO_DIR/../CAMWOSA-wiki}"
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

if [ ! -d "$WIKI_DIR/.git" ]; then
    echo "ERROR: Wiki-Repo nicht gefunden in $WIKI_DIR"
    echo "Bitte erst clonen: git clone https://github.com/MadGapun/CAMWOSA.wiki.git $WIKI_DIR"
    exit 1
fi

echo "==> Pull neuester Stand des Wiki-Repos"
( cd "$WIKI_DIR" && git pull --quiet )

echo "==> Kopiere alle docs/wiki/*.md nach $WIKI_DIR"
cp -f "$REPO_DIR/docs/wiki/"*.md "$WIKI_DIR/"

echo "==> Schreibe relative Code-Links in absolute GitHub-URLs"
cd "$WIKI_DIR"
for f in *.md; do
    [ "$f" = "_Sidebar.md" ] && continue
    [ "$f" = "_Footer.md" ] && continue
    sed -i 's|(\.\./\.\./backend/|(https://github.com/MadGapun/CAMWOSA/blob/main/backend/|g' "$f"
    sed -i 's|(\.\./\.\./frontend/|(https://github.com/MadGapun/CAMWOSA/blob/main/frontend/|g' "$f"
    sed -i 's|(\.\./\.\./electron/|(https://github.com/MadGapun/CAMWOSA/blob/main/electron/|g' "$f"
    sed -i 's|(\.\./\.\./mcp_server/|(https://github.com/MadGapun/CAMWOSA/blob/main/mcp_server/|g' "$f"
    sed -i 's|(\.\./\.\./data/|(https://github.com/MadGapun/CAMWOSA/blob/main/data/|g' "$f"
    sed -i 's|(\.\./SPECIFICATION\.md)|(https://github.com/MadGapun/CAMWOSA/blob/main/docs/SPECIFICATION.md)|g' "$f"
    sed -i 's|(\.\./ROTARY\.md)|(https://github.com/MadGapun/CAMWOSA/blob/main/docs/ROTARY.md)|g' "$f"
    # Wiki-interne Links ohne .md
    sed -i 's|\](\([A-Za-z0-9_-]*\)\.md)|](\1)|g' "$f"
done

# Sidebar + Footer NICHT ueberschreiben wenn schon vorhanden
if [ ! -f _Sidebar.md ]; then
    echo "==> _Sidebar.md fehlt, lege Default an"
    cat > _Sidebar.md <<'EOSB'
### Übersicht
- [Home](Home)
- [Master-Plan](Master-Plan)
- [Architektur](Architektur)
- [Glossar](Glossar)
- [Contribution](Contribution)
EOSB
fi

if [ $DRY -eq 1 ]; then
    echo "==> DRY-RUN, kein commit/push. Diff:"
    git diff --stat
    exit 0
fi

echo "==> Commit + Push"
git add -A
if git diff --cached --quiet; then
    echo "Keine Aenderungen — Wiki ist aktuell."
    exit 0
fi
git commit -q -m "Wiki-Sync aus docs/wiki/ (skript)"
git push origin master
echo "Fertig."
