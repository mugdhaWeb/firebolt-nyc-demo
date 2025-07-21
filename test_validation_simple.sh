#!/bin/bash

set -e

echo "🧪 Testing validation function..."

# Create or clear the log
precache_log="precache.log"
> "$precache_log"

# Simple validation function
validate_query_simple() {
    local query_name="$1"
    local query="$2"
    
    echo "Testing query: $query_name"
    
    # Execute query
    local result=$(docker exec firebolt-core fb -C -c "$query" 2>/dev/null)
    local exit_code=$?
    
    echo "Exit code: $exit_code"
    echo "Raw result:"
    echo "$result"
    echo "---"
    
    # Simple row counting - just check if we have meaningful data
    local has_data=0
    if [[ $exit_code -eq 0 && -n "$result" ]]; then
        if echo "$result" | grep -q -E '[0-9]{2,}'; then
            has_data=1
            echo "✅ Found data with numbers"
        else
            echo "❌ No significant data found"
        fi
    else
        echo "❌ Query failed or returned empty"
    fi
    
    # Log result
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    if [[ $has_data -eq 1 ]]; then
        echo "$timestamp | $query_name | ✅ SUCCESS | data found" >> "$precache_log"
        echo "✅ $query_name: SUCCESS"
        return 0
    else
        echo "$timestamp | $query_name | ❌ FAILED | no data" >> "$precache_log"
        echo "❌ $query_name: FAILED"
        return 1
    fi
}

# Test the 5 main queries
echo "Testing Q1..."
validate_query_simple "Q1" "SELECT COUNT(*) as total_violations FROM violations WHERE calculated_fine_amount > 0"

echo ""
echo "Testing Q2..."
validate_query_simple "Q2" "SELECT street_name, COUNT(*) as total_violations FROM violations WHERE street_name IS NOT NULL AND street_name != '' GROUP BY street_name ORDER BY street_name DESC LIMIT 5"

echo ""
echo "Testing Q3..."
validate_query_simple "Q3" "SELECT vehicle_make, COUNT(*) as violations FROM violations WHERE vehicle_make IS NOT NULL GROUP BY vehicle_make ORDER BY violations DESC LIMIT 5"

echo ""
echo "Testing Q4..."
validate_query_simple "Q4" "SELECT EXTRACT(YEAR FROM issue_date) as year, COUNT(*) as violation_count FROM violations WHERE issue_date IS NOT NULL GROUP BY EXTRACT(YEAR FROM issue_date) ORDER BY year LIMIT 5"

echo ""
echo "Testing Q5..."
validate_query_simple "Q5" "SELECT summons_number, street_name, calculated_fine_amount FROM violations WHERE calculated_fine_amount > 0 ORDER BY calculated_fine_amount DESC LIMIT 10"

echo ""
echo "📋 Validation Results:"
cat "$precache_log"

echo ""
success_count=$(grep -c "✅ SUCCESS" "$precache_log" 2>/dev/null || echo "0")
echo "✅ Successful queries: $success_count/5"

if [[ $success_count -eq 5 ]]; then
    echo "🎉 All queries validated successfully!"
    exit 0
else
    echo "❌ Some queries failed validation"
    exit 1
fi 