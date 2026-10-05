#!/usr/bin/env bash
# Build the public site (landing page + slides) into dist/ and publish it to the gh-pages branch.
#
#   tools/publicar.sh               build and push to gh-pages
#   tools/publicar.sh --cloudflare  build and deploy to Cloudflare (wrangler.jsonc)
#   tools/publicar.sh --local       build only
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo"

slides/build.sh < /dev/null
rm -rf dist
mkdir -p dist/img
cp web/index.html slides/clase.html dist/
cp slides/img/*.png slides/img/*.svg slides/img/*.gif dist/img/
cp -r slides/img/loop dist/img/loop
touch dist/.nojekyll

if [ "${1:-}" = "--local" ]; then
    echo "listo: dist/index.html"
    exit 0
fi

if [ "${1:-}" = "--cloudflare" ]; then
    npx --yes wrangler@4 deploy
    exit 0
fi

remote="$(git remote get-url origin)"
cd dist
git init -q -b gh-pages
git add -A
git -c user.name="$(git -C "$repo" config user.name)" -c user.email="$(git -C "$repo" config user.email)" \
    commit -q -m "site: $(git -C "$repo" rev-parse --short HEAD)"
git push -q --force "$remote" gh-pages
rm -rf .git
echo "publicado: rama gh-pages"
