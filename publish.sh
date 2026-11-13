#!/bin/zsh
# Builds the site and publishes it to GitHub Pages:  ./publish.sh "what changed"
# The project is saved to the main branch; the public/ folder is what GitHub Pages serves (branch gh-pages).
set -e
cd "${0:A:h}"
python3 build.py
git add -A
git diff --cached --quiet || git commit -m "${1:-Update the site}"
git push origin main
git push origin "$(git subtree split --prefix public main)":refs/heads/gh-pages --force
echo "published; the site updates in a minute or two"
