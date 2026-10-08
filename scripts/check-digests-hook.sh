#!/bin/bash
# Pre-commit hook to prevent committing placeholder digests
# Install: cp scripts/check-digests-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

DIGEST_FILE="binary_digests.txt"

if [ -f "$DIGEST_FILE" ]; then
    if grep -q "PLACEHOLDER_DIGEST_MUST_BE_REPLACED_BEFORE_BUILD" "$DIGEST_FILE"; then
        echo "ERROR: Cannot commit $DIGEST_FILE with placeholder digests"
        echo ""
        echo "Please initialize the digests first:"
        echo "  python3 scripts/compute_binary_digests.py"
        echo ""
        echo "Then review and stage the updated file."
        exit 1
    fi
fi

exit 0
