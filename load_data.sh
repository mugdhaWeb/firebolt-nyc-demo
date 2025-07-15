#!/bin/bash

set -e

echo "🔄 Loading NYC Parking Violations Data"
echo "======================================="

# Check if Firebolt Core is running
if ! docker exec firebolt-core fb -C -c "SELECT 1" >/dev/null 2>&1; then
    echo "❌ Firebolt Core is not running. Please run ./setup_core.sh first."
    exit 1
fi

echo "📋 Step 1: Creating violations table..."
docker exec firebolt-core fb -C -c "DROP TABLE IF EXISTS violations"
docker exec firebolt-core fb -C -c "CREATE TABLE violations (
    summons_number BIGINT,
    plate_id STRING,
    registration_state STRING,
    issue_date DATE,
    violation_code INT,
    vehicle_make STRING,
    street_name STRING,
    fine_amount DOUBLE
) PRIMARY INDEX summons_number"

echo "📥 Step 2: Loading data from S3 (this takes ~30-60 seconds)..."
docker exec firebolt-core fb -C -c "COPY INTO violations FROM 's3://firebolt-sample-datasets-public-us-east-1/nyc_sample_datasets/nycparking/parquet/' WITH PATTERN='*.parquet' TYPE=PARQUET"

echo "💰 Step 3: Adding calculated fine amounts..."
docker exec firebolt-core fb -C -c "ALTER TABLE violations ADD COLUMN calculated_fine_amount DOUBLE"

docker exec firebolt-core fb -C -c "UPDATE violations SET calculated_fine_amount = CASE 
    WHEN violation_code = 36 THEN 65.0
    WHEN violation_code = 21 THEN 115.0
    WHEN violation_code = 38 THEN 35.0
    WHEN violation_code = 37 THEN 60.0
    WHEN violation_code = 20 THEN 95.0
    WHEN fine_amount > 0 THEN fine_amount
    ELSE 50.0
END"

echo "🎯 Step 4: Creating performance indexes..."
docker exec firebolt-core fb -C -c "CREATE SPARSE INDEX idx_street ON violations (street_name)"
docker exec firebolt-core fb -C -c "CREATE SPARSE INDEX idx_date ON violations (issue_date)"
docker exec firebolt-core fb -C -c "CREATE SPARSE INDEX idx_make ON violations (vehicle_make)"
docker exec firebolt-core fb -C -c "CREATE SPARSE INDEX idx_fine ON violations (calculated_fine_amount)"

echo "✅ Step 5: Verifying data loading..."
result=$(docker exec firebolt-core fb -C -c "SELECT 
    COUNT(*) as total_violations,
    COUNT(DISTINCT street_name) as unique_streets,
    COUNT(DISTINCT vehicle_make) as unique_makes,
    ROUND(AVG(calculated_fine_amount), 2) as avg_fine
FROM violations")

echo ""
echo "🎉 Data loading completed successfully!"
echo "📊 Results:"
echo "$result"
echo ""
echo "🚀 You can now run: streamlit run app/streamlit_app.py" 