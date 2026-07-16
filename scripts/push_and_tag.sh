#!/bin/bash
# RFQ2BOQ Git Push Script — Run this to push all commits and tags
# Last updated: 2026-05-19

set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "RFQ2BOQ — Git Push & Handover"
echo "=========================================="
echo ""

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "ERROR: No remote 'origin' found. Run: git remote add origin https://github.com/Srujan0798/rfq2boq.git"
    exit 1
fi

echo "Remote: $(git remote get-url origin)"
echo "Commits ahead of origin/main: $(git log --oneline origin/main..HEAD | wc -l)"
echo ""

# Show what will be pushed
echo "Recent commits to push:"
git log --oneline origin/main..HEAD | head -5
echo ""

# Push all commits
echo "=========================================="
echo "Pushing commits to origin/main..."
echo "=========================================="
git push origin main

# Push pre-week-1 tag
echo ""
echo "=========================================="
echo "Pushing pre-week-1 tag..."
echo "=========================================="
git push origin pre-week-1

# Tag v1.0-handover
echo ""
echo "=========================================="
echo "Creating v1.0-handover tag..."
echo "=========================================="
git tag -a v1.0-handover -m "RFQ2BOQ v1.0 — Internship complete. READY WITH CAVEATS. Real F1 0.523. All deliverables shipped."
git push origin v1.0-handover

echo ""
echo "=========================================="
echo "✅ ALL PUSHED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "Tags pushed:"
git tag | grep -E "week|handover|v1"
echo ""
echo "Run 'git log --oneline origin/main..HEAD' to verify all commits are pushed."
echo "Run 'git ls-remote origin refs/tags/v1.0-handover' to verify the tag exists remotely."
