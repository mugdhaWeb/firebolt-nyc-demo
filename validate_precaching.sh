#!/bin/bash

set -e

echo "🤖 Precache-QA-Bot CI Validation"
echo "=================================="

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Check if required dependencies are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not found"
    exit 1
fi

# Make test script executable
chmod +x test_precache_validation.py

# Run the comprehensive test suite
echo "🧪 Running Precache-QA-Bot validation..."
echo ""

# Execute the test with timeout
timeout 600 python3 test_precache_validation.py
exit_code=$?

echo ""
echo "=================================="

if [ $exit_code -eq 0 ]; then
    echo "🎉 CI VALIDATION PASSED"
    echo "✅ All precaching tests completed successfully"
    echo "✅ load_data.sh properly validates and caches queries"
    echo "✅ No empty results detected"
    echo "✅ Performance requirements met"
    
    # Show summary if logs exist
    if [ -f "precache.log" ]; then
        echo ""
        echo "📊 Quick Summary:"
        success_count=$(grep -c "✅ SUCCESS" precache.log 2>/dev/null || echo "0")
        echo "   • Successful queries: $success_count"
        
        if [ -f "ci_run.log" ]; then
            exec_time=$(grep "Execution time:" ci_run.log 2>/dev/null | cut -d: -f2 | tr -d ' ' || echo "unknown")
            echo "   • Total execution time: $exec_time"
        fi
    fi
    
elif [ $exit_code -eq 124 ]; then
    echo "❌ CI VALIDATION TIMED OUT"
    echo "The validation process exceeded 10 minutes"
    
elif [ $exit_code -eq 130 ]; then
    echo "⚠️  CI VALIDATION INTERRUPTED"
    echo "The validation process was interrupted"
    
else
    echo "❌ CI VALIDATION FAILED"
    echo "One or more precaching tests failed"
    echo "Check precache.log and ci_run.log for details"
fi

echo ""
echo "Log files:"
[ -f "precache.log" ] && echo "  📄 precache.log (validation results)"
[ -f "ci_run.log" ] && echo "  📄 ci_run.log (full execution log)"

exit $exit_code 