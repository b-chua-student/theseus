set -eu

chunk="$RUNNER_TEMP/dora-report/summary/$DORA_SUMMARY_GROUP-$1.md"
if [[ -f "$chunk" ]]; then
    cat "$chunk" >> "$GITHUB_STEP_SUMMARY"
fi
