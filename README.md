# Firebolt Core NYC Parking Demo

Analyze 21.5 million New York City parking violations with sub‑second queries using Firebolt Core's high-performance analytical database.

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Testing & Validation](#testing--validation)
7. [Troubleshooting](#troubleshooting)
8. [Performance](#performance)
9. [Data Schema](#data-schema)
10. [Architecture](#architecture)

## Features

* **Sub‑second analytical queries** on 21.5 million NYC parking violations
* **Interactive Streamlit dashboard** with real-time filtering and visualizations
* **Comprehensive precaching** ensures guaranteed <200ms query performance
* **5 analytical benchmark queries** demonstrating typical BI patterns:
  - **Q1**: Aggregation statistics (COUNT, SUM, AVG, MIN, MAX)
  - **Q2**: Revenue analysis by street with GROUP BY operations
  - **Q3**: Vehicle make analysis with multi-column aggregations
  - **Q4**: Time series analysis with date extraction
  - **Q5**: Interactive filtering with dynamic WHERE clauses
* **Automated validation** and testing scripts for production readiness
* **Intelligent query optimization** with sparse and aggregating indexes
* **Real‑time performance monitoring** with execution timing and row counts

## Prerequisites

* **Docker Engine** with at least 16 GB RAM allocation
* **Python 3.11** or later
* macOS, Linux, or Windows 10/11 with WSL 2
* **8+ GB available disk space** for data and containers
* **Reliable internet connection** to download ~500MB compressed dataset

## Quick Start

**Complete setup in 3 steps:**

```bash
# 1. Setup Firebolt Core container
./setup_core.sh --auto-run

# 2. Load NYC parking data with precaching
./load_data.sh

# 3. Launch dashboard
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

**Verify everything works:**
```bash
python3 test_precache_validation.py  # All tests should pass
```

Open http://localhost:8501 and click any query button to see sub-200ms performance!

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/firebolt-db/firebolt-nyc-demo.git
cd firebolt-nyc-demo
```

### 2. Setup Firebolt Core
```bash
chmod +x setup_core.sh
./setup_core.sh --auto-run
# Watch for: "Firebolt Core is ready and responding!"
```

### 3. Load Data
```bash
chmod +x load_data.sh
./load_data.sh
# Expect: "Data loading completed successfully!"
```

The data loading process includes:
- Downloading 21.5M records from S3 (~500MB compressed parquet)
- Creating optimized table schema with 50+ columns
- Building sparse indexes on key columns (issue_date, street_name, vehicle_make)
- **Precaching all analytical queries** for guaranteed sub-200ms performance
- Comprehensive validation to ensure all queries return >0 rows

### 4. Setup Python Environment
```bash
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Launch Dashboard
```bash
streamlit run app/streamlit_app.py
# Open http://localhost:8501 in your browser
```

## Usage

### Dashboard Overview

The Streamlit dashboard features three main tabs:

#### 🏃 Run Benchmarks
- Execute 5 analytical queries with real-time timing
- Dynamic filtering by street name, vehicle make, and fine amount
- Custom SQL query execution with optional filter application
- Results tracking with execution history

#### 📊 Visualizations  
- Auto-generated Plotly charts based on query results
- Bar charts for revenue analysis and vehicle statistics
- Line charts for time series trends
- Scatter plots for interactive filtering results
- Metrics displays for key statistics

#### 🔍 Browse Data
- Sample data exploration (latest 100 records)
- Dataset statistics and metadata
- Real-time data refresh capabilities

### Direct SQL Access

```bash
# Interactive SQL shell
docker exec -it firebolt-core fb -C

# Example queries
SELECT COUNT(*) FROM violations;
SELECT street_name, SUM(calculated_fine_amount) 
FROM violations 
GROUP BY street_name 
ORDER BY SUM(calculated_fine_amount) DESC 
LIMIT 10;
```

### Available Scripts

```bash
./setup_core.sh         # Initialize Firebolt Core container
./load_data.sh          # Load NYC data with precaching
./check_status.sh       # Verify system status
./validate_precaching.sh # Run comprehensive validation
./test_validation_simple.sh # Quick query validation
./cleanup.sh            # Clean up containers and data
```

## Testing & Validation

### Comprehensive Validation Suite

**Run the full test suite:**
```bash
python3 test_precache_validation.py
```

This validates:
- ✅ Firebolt Core connectivity
- ✅ Data loading completion (21.5M+ records)
- ✅ All 9 queries execute successfully with >0 results
- ✅ Performance requirements met (<1s for most queries)
- ✅ No empty result violations
- ✅ Precache log integrity

**Quick validation:**
```bash
./test_validation_simple.sh  # Tests core queries only
```

**Expected output for successful validation:**
```
🎉 All tests passed! Precaching is working correctly.
✅ Successful queries: 9/9
⏱️  Total precache time: 1.145s
📊 Average query time: 0.127s
```

### Performance Benchmarks

All queries should execute in **<200ms** after precaching:

| Query | Description | Expected Time | Row Count |
|-------|-------------|---------------|-----------|
| Q1 | Aggregation statistics | <100ms | 1 row |
| Q2 | Revenue by street | <200ms | 10 rows |
| Q3 | Vehicle make analysis | <200ms | 10 rows |
| Q4 | Yearly trend analysis | <150ms | ~15 rows |
| Q5 | Interactive filtering | <200ms | 100 rows |

## Troubleshooting

### Common Issues

**1. Container not starting:**
```bash
# Check Docker memory allocation (need 16GB+)
docker system df
# Restart Docker Desktop if needed
./cleanup.sh && ./setup_core.sh --auto-run
```

**2. Data loading fails:**
```bash
# Check internet connectivity and retry
curl -I https://firebolt-publishing-public.s3.amazonaws.com/
./load_data.sh
```

**3. Queries returning empty results:**
```bash
# Verify data loaded correctly
docker exec firebolt-core fb -C -c "SELECT COUNT(*) FROM violations;"
# Should return 21563502
```

**4. Port conflicts:**
```bash
# Kill existing Streamlit processes
lsof -ti:8501 | xargs kill -9
# Or use different port
streamlit run app/streamlit_app.py --server.port 8502
```

**5. Performance issues:**
```bash
# Check if precaching completed
grep "SUCCESS" precache.log | wc -l  # Should be 9
# Re-run precaching
./load_data.sh  # Will re-precache automatically
```

### Diagnostic Commands

```bash
./check_status.sh                    # Overall system status
docker logs firebolt-core --tail 20  # Container logs  
docker stats firebolt-core           # Resource usage
python3 test_precache_validation.py  # Comprehensive testing
```

## Performance

### Query Performance Targets

- **Primary queries (Q1-Q5)**: <200ms each
- **Filter queries**: <100ms each  
- **Data loading**: ~60-90 seconds total
- **Precaching**: ~1-2 seconds for all queries

### Optimization Features

- **Sparse indexes** on `issue_date`, `street_name`, `vehicle_make`, `violation_code`
- **Query precaching** during data load ensures consistent performance
- **Streamlit caching** with TTL for filter data
- **Optimized data types** and table structure for analytical workloads

## Data Schema

### violations Table (21,563,502 rows)

Key columns include:
- `summons_number` (TEXT) - Unique violation identifier
- `plate_id` (TEXT) - License plate 
- `registration_state` (TEXT) - State of registration
- `issue_date` (DATE) - When violation was issued
- `violation_code` (INT) - Type of violation  
- `vehicle_make` (TEXT) - Vehicle manufacturer
- `street_name` (TEXT) - Location of violation
- `fine_amount` (REAL) - Original fine amount
- `calculated_fine_amount` (REAL) - Business logic applied fine
- Plus 40+ additional columns for comprehensive analysis

### Data Source
- **NYC Open Data**: Parking violations dataset
- **Format**: Parquet files optimized for analytics  
- **Size**: ~500MB compressed, ~2GB uncompressed
- **Location**: Public S3 bucket
- **Update Frequency**: Static historical dataset

## Architecture

### Components

1. **Firebolt Core Container**: High-performance analytical database
2. **Data Pipeline**: S3 → Parquet → Firebolt ingestion
3. **Streamlit App**: Interactive dashboard and query interface  
4. **Validation Suite**: Automated testing and performance monitoring
5. **Helper Scripts**: Setup, maintenance, and troubleshooting tools

### Data Flow

```
S3 Parquet Files → Docker Container → Firebolt Core → Indexing → 
Precaching → Validation → Streamlit Dashboard → User Interaction
```

### Technology Stack

- **Database**: Firebolt Core (containerized)
- **Frontend**: Streamlit with Plotly visualizations
- **Data Processing**: pandas, NumPy for data manipulation
- **Container**: Docker for deployment consistency
- **Validation**: Python testing framework with comprehensive checks

---

## Cleanup

When finished, free disk space and stop all containers:

```bash
./cleanup.sh
```

This removes:
- Firebolt Core container
- Downloaded data files  
- Python virtual environment
- Docker volumes and networks

Perfect for shared development environments!