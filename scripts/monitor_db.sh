#!/bin/bash
# scripts/monitor_db.sh
# Monitor SQLite database size and table counts

set -euo pipefail

DB_PATH="${DB_PATH:-db/recruitment_assistant.db}"
THRESHOLD_MB=${THRESHOLD_MB:-100}

if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found at $DB_PATH"
    exit 1
fi

echo "=== Database Monitoring Report ==="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Database: $DB_PATH"
echo ""

# File size
DB_SIZE_MB=$(du -m "$DB_PATH" | cut -f1)
echo "📊 Total Size: $DB_SIZE_MB MB"

if [ "$DB_SIZE_MB" -gt "$THRESHOLD_MB" ]; then
    echo "⚠️  WARNING: Database exceeds threshold ($THRESHOLD_MB MB)"
fi

echo ""
echo "📋 Table Statistics:"
echo "────────────────────────────────────────"

sqlite3 "$DB_PATH" << EOF
SELECT 
  name as 'Table Name',
  (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name = t.name) as 'Row Count',
  ROUND(page_count * page_size / 1024.0 / 1024.0, 2) as 'Size (MB)'
FROM (
  SELECT 'offers_raw' as name UNION
  SELECT 'offer_keywords' UNION
  SELECT 'my_experiences' UNION
  SELECT 'my_projects' UNION
  SELECT 'matching_scores' UNION
  SELECT 'generations' UNION
  SELECT 'archive_manifest'
) t, pragma_page_count(), pragma_page_size()
WHERE name = 'offers_raw'
ORDER BY name;
EOF

echo ""
echo "📈 Detailed Table Counts:"
echo "────────────────────────────────────────"

sqlite3 "$DB_PATH" << EOF
.mode column
.headers on
SELECT 'offers_raw' as table_name, COUNT(*) as count FROM offers_raw
UNION ALL
SELECT 'offer_keywords', COUNT(*) FROM offer_keywords
UNION ALL
SELECT 'my_experiences', COUNT(*) FROM my_experiences
UNION ALL
SELECT 'my_projects', COUNT(*) FROM my_projects
UNION ALL
SELECT 'matching_scores', COUNT(*) FROM matching_scores
UNION ALL
SELECT 'generations', COUNT(*) FROM generations
UNION ALL
SELECT 'archive_manifest', COUNT(*) FROM archive_manifest;
EOF

echo ""
echo "🗂️  Archive Summary:"
echo "────────────────────────────────────────"

sqlite3 "$DB_PATH" << EOF
SELECT 
  year,
  month,
  tier,
  COUNT(*) as count,
  COUNT(DISTINCT country) as countries,
  COUNT(DISTINCT company) as companies
FROM archive_manifest
GROUP BY year, month, tier
ORDER BY year DESC, month DESC;
EOF

echo ""
echo "✅ Report generated successfully"
