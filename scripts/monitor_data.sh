#!/bin/bash
# scripts/monitor_data.sh
# Monitor data/offers/ directory size and file count

set -euo pipefail

DATA_PATH="${DATA_PATH:-data/offers}"
THRESHOLD_MB=${THRESHOLD_MB:-500}

if [ ! -d "$DATA_PATH" ]; then
    echo "❌ Data directory not found at $DATA_PATH"
    exit 1
fi

echo "=== Data Monitoring Report ==="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Directory: $DATA_PATH"
echo ""

# Overall size
TOTAL_SIZE=$(du -sh "$DATA_PATH" | cut -f1)
TOTAL_SIZE_MB=$(du -m "$DATA_PATH" | cut -f1)

echo "📊 Total Size: $TOTAL_SIZE ($TOTAL_SIZE_MB MB)"

if [ "$TOTAL_SIZE_MB" -gt "$THRESHOLD_MB" ]; then
    echo "⚠️  WARNING: Data exceeds threshold ($THRESHOLD_MB MB)"
fi

echo ""
echo "📋 File Count:"
echo "────────────────────────────────────────"

TOTAL_FILES=$(find "$DATA_PATH" -type f | wc -l)
TOTAL_DIRS=$(find "$DATA_PATH" -type d | wc -l)

echo "Total files: $TOTAL_FILES"
echo "Total directories: $TOTAL_DIRS"

echo ""
echo "📈 Breakdown by Tier & Country:"
echo "────────────────────────────────────────"

find "$DATA_PATH" -type d -name "tier-*" -prune | while read tier_dir; do
    TIER=$(basename "$tier_dir")
    TIER_SIZE=$(du -sh "$tier_dir" 2>/dev/null | cut -f1 || echo "0B")
    TIER_FILES=$(find "$tier_dir" -type f 2>/dev/null | wc -l)
    echo "$TIER: $TIER_SIZE ($TIER_FILES files)"
    
    find "$tier_dir" -maxdepth 1 -type d | while read country_dir; do
        if [ "$country_dir" != "$tier_dir" ]; then
            COUNTRY=$(basename "$country_dir")
            COUNTRY_SIZE=$(du -sh "$country_dir" 2>/dev/null | cut -f1 || echo "0B")
            echo "  ├─ $COUNTRY: $COUNTRY_SIZE"
        fi
    done
done

echo ""
echo "🗓️  Breakdown by Year/Quarter:"
echo "────────────────────────────────────────"

if [ -d "$DATA_PATH" ]; then
    for year_dir in $(find "$DATA_PATH" -maxdepth 1 -type d -name "20*" | sort -r); do
        YEAR=$(basename "$year_dir")
        YEAR_SIZE=$(du -sh "$year_dir" | cut -f1)
        echo "$YEAR: $YEAR_SIZE"
        
        for quarter_dir in $(find "$year_dir" -maxdepth 1 -type d -name "Q*" | sort); do
            QUARTER=$(basename "$quarter_dir")
            QUARTER_SIZE=$(du -sh "$quarter_dir" | cut -f1)
            QUARTER_FILES=$(find "$quarter_dir" -type f | wc -l)
            echo "  ├─ $QUARTER: $QUARTER_SIZE ($QUARTER_FILES files)"
        done
    done
fi

echo ""
echo "🧹 Cleanup Recommendations:"
echo "────────────────────────────────────────"

# Find large files
echo "Largest files (top 5):"
find "$DATA_PATH" -type f -exec du -h {} + 2>/dev/null | sort -rh | head -5 | sed 's/^/  /'

echo ""
echo "✅ Report generated successfully"
