#!/bin/bash
# Script to purge sensitive file from git history
# This removes the file from all commits in the repository

set -e

FILE_TO_PURGE="inputs/vmware-inv.xlsx"

echo "🗑️  Purging file from git history: $FILE_TO_PURGE"
echo ""
echo "⚠️  WARNING: This will rewrite git history!"
echo "   - All commit hashes will change"
echo "   - Force push will be required"
echo "   - Collaborators will need to re-clone"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    echo ""
    echo "❌ git-filter-repo is not installed."
    echo ""
    echo "Install with:"
    echo "  brew install git-filter-repo"
    echo "  # or"
    echo "  pip install git-filter-repo"
    exit 1
fi

# Create backup
BACKUP_DIR="../inv-vmware-opa-backup-$(date +%Y%m%d-%H%M%S)"
echo ""
echo "📦 Creating backup in: $BACKUP_DIR"
cd ..
cp -r inv-vmware-opa "$BACKUP_DIR"
cd inv-vmware-opa

echo ""
echo "🔍 Checking if file exists in history..."
if git log --all --full-history -- "$FILE_TO_PURGE" | grep -q "commit"; then
    echo "   ✓ File found in history"
else
    echo "   ℹ️  File not found in git history"
    exit 0
fi

echo ""
echo "🔧 Removing file from all commits..."
git filter-repo --path "$FILE_TO_PURGE" --invert-paths --force

echo ""
echo "✅ File purged from git history!"
echo ""
echo "📊 Statistics:"
git count-objects -vH

echo ""
echo "🔄 Next steps:"
echo "   1. Verify the repository:"
echo "      git log --all --oneline"
echo "      git --no-pager log --all -- $FILE_TO_PURGE"
echo ""
echo "   2. Add file to .gitignore:"
echo "      echo '$FILE_TO_PURGE' >> .gitignore"
echo "      git add .gitignore"
echo "      git commit -m 'chore: add sensitive file to gitignore'"
echo ""
echo "   3. Force push to remote:"
echo "      git push origin --force --all"
echo "      git push origin --force --tags"
echo ""
echo "⚠️  Backup saved at: $BACKUP_DIR"
