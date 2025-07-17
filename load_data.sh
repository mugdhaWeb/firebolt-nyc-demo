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

echo "🔥 Step 5: Enabling engine optimization features..."
# Enable AUTO_WARMUP for proactive data fetching
docker exec firebolt-core fb -C -c "ALTER ENGINE SET AUTO_WARMUP = true" >/dev/null 2>&1 || true

echo "✅ Step 6: Verifying data loading..."
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

# Background optimization queries (run silently to pre-cache data for optimal user experience)
# Cache filter data queries - these match the Streamlit app's get_filter_data function
docker exec firebolt-core fb -C -c "SELECT DISTINCT street_name FROM violations WHERE street_name IS NOT NULL AND street_name != '' ORDER BY street_name" >/dev/null 2>&1 &
docker exec firebolt-core fb -C -c "SELECT DISTINCT calculated_fine_amount FROM violations WHERE calculated_fine_amount IS NOT NULL AND calculated_fine_amount > 0 ORDER BY calculated_fine_amount" >/dev/null 2>&1 &
docker exec firebolt-core fb -C -c "SELECT DISTINCT vehicle_make FROM violations WHERE vehicle_make IS NOT NULL AND LENGTH(vehicle_make) >= 2 AND vehicle_make != '' ORDER BY vehicle_make" >/dev/null 2>&1 &

# Cache benchmark queries - these match the Streamlit app's BENCHMARK_QUERIES
docker exec firebolt-core fb -C -c "SELECT COUNT(*) as total_violations, SUM(calculated_fine_amount) as total_fines, AVG(calculated_fine_amount) as avg_fine, MIN(calculated_fine_amount) as min_fine, MAX(calculated_fine_amount) as max_fine FROM violations WHERE calculated_fine_amount > 0" >/dev/null 2>&1 &
docker exec firebolt-core fb -C -c "SELECT street_name, COUNT(*) as total_violations, SUM(calculated_fine_amount) as total_revenue, AVG(calculated_fine_amount) as avg_fine FROM violations WHERE street_name IS NOT NULL AND street_name != '' AND calculated_fine_amount > 0 GROUP BY street_name ORDER BY total_revenue DESC LIMIT 10" >/dev/null 2>&1 &
docker exec firebolt-core fb -C -c "SELECT vehicle_make, COUNT(*) as violations, AVG(calculated_fine_amount) as avg_fine, SUM(calculated_fine_amount) as total_fines FROM violations WHERE vehicle_make IS NOT NULL AND calculated_fine_amount > 0 GROUP BY vehicle_make ORDER BY violations DESC LIMIT 10" >/dev/null 2>&1 &
docker exec firebolt-core fb -C -c "SELECT EXTRACT(YEAR FROM issue_date) as year, COUNT(*) as violation_count, SUM(calculated_fine_amount) as total_revenue, AVG(calculated_fine_amount) as avg_fine FROM violations WHERE issue_date IS NOT NULL AND calculated_fine_amount > 0 AND EXTRACT(YEAR FROM issue_date) BETWEEN 2010 AND 2024 GROUP BY EXTRACT(YEAR FROM issue_date) ORDER BY year" >/dev/null 2>&1 &

# Cache sample data query
docker exec firebolt-core fb -C -c "SELECT summons_number, plate_id, registration_state, issue_date, vehicle_make, street_name, calculated_fine_amount FROM violations ORDER BY issue_date DESC LIMIT 100" >/dev/null 2>&1 &

# Wait for background optimization queries to complete
wait

echo ""
echo "🚀 Engine optimization complete - demo ready for optimal performance!"
echo "🚀 You can now run: streamlit run app/streamlit_app.py" 