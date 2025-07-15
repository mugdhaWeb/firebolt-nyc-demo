# 🚗 Firebolt Core NYC Parking Demo

**Explore 20+ million NYC parking violations with sub-second analytics!**

This demo showcases [Firebolt Core's](https://github.com/firebolt-db/firebolt-core) high-performance distributed query engine using real NYC parking violations data. Experience lightning-fast analytics on massive datasets with an interactive Streamlit interface.

## ✨ Features

- 🚀 **Sub-second query performance** on 20M+ rows
- 📊 **Interactive visualizations** with Plotly
- 🎯 **Real-time benchmarking** with performance monitoring
- 🔍 **Query plan analysis** showing index optimizations
- 📈 **5 analytical workloads** demonstrating different use cases
- 🛠️ **Easy one-command setup** 

## 🎯 Quick Start

**Prerequisites:**
- Docker Engine with 16GB+ RAM
- Python 3.11+
- Linux kernel >= 6.1 (for Docker host)

### One-Command Bootstrap

```bash
# Clone and setup everything
git clone <this-repo>
cd firebolt-nyc-demo

# Setup Firebolt Core, load data, and start the app
make all
```

**🔧 Quick Debug Commands:**
```bash
make debug    # Show detailed diagnostics
make fix      # Fix common connectivity issues 
make status   # Check if everything is running
```

### Manual Setup

1. **Start Firebolt Core (Terminal 1):**
   ```bash
   # Make setup script executable
   chmod +x setup_core.sh
   
   # Start Firebolt Core
   ./setup_core.sh
   ```
   
   **✅ Wait for**: "Firebolt Core is ready!" message before proceeding.

2. **Prepare the dataset (Terminal 1):**
   ```bash
   # Create Python virtual environment
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Prepare dataset metadata
   python scripts/download_dataset.py
   ```

3. **Load data and create indexes (Terminal 1):**
   
   **⚠️ IMPORTANT: Memory Requirements**
   Loading the full NYC dataset (~2-5 million rows) requires significant memory. If you encounter "Out of memory" errors:
   
   **Option A: Create test data (recommended for systems with <16GB RAM):**
   ```bash
   # Create a simple test table with sample data
   docker exec firebolt-core fb -C -c "CREATE TABLE violations_test (id INT, street_name STRING, fine_amount DOUBLE) PRIMARY INDEX id"
   docker exec firebolt-core fb -C -c "INSERT INTO violations_test VALUES (1, 'Broadway', 50.0), (2, 'Main St', 75.0), (3, 'Wall St', 100.0)"
   docker exec firebolt-core fb -C -c "SELECT * FROM violations_test"
   ```
   
   **Option B: Try loading real data (requires 16GB+ RAM):**
   ```bash
   # Create the table first
   docker exec firebolt-core fb -C -c "CREATE TABLE violations ( summons_number BIGINT, plate_id STRING, registration_state STRING, plate_type STRING, issue_date DATE, violation_code INT, vehicle_body_type STRING, vehicle_make STRING, issuing_agency STRING, street_code1 INT, street_code2 INT, street_code3 INT, vehicle_expiration_date DATE, violation_location STRING, violation_precinct INT, issuer_precinct INT, issuer_code INT, issuer_command STRING, issuer_squad STRING, violation_time STRING, time_first_observed STRING, violation_county STRING, violation_in_front_of_or_opposite STRING, house_number STRING, street_name STRING, intersecting_street STRING, date_first_observed DATE, law_section INT, sub_division STRING, violation_legal_code STRING, days_parking_in_effect STRING, from_hours_in_effect STRING, to_hours_in_effect STRING, vehicle_color STRING, unregistered_vehicle STRING, vehicle_year INT, meter_number STRING, feet_from_curb INT, violation_post_code STRING, violation_description STRING, no_standing_or_stopping_violation STRING, hydrant_violation STRING, double_parking_violation STRING, latitude DOUBLE, longitude DOUBLE, community_board INT, community_council INT, census_tract INT, bin INT, bbl BIGINT, nta STRING, fine_amount DOUBLE ) PRIMARY INDEX summons_number"
   
   # Try loading with auto-create (may fail due to memory constraints)
   docker exec firebolt-core fb -C -c "COPY INTO violations FROM 's3://firebolt-sample-datasets-public-us-east-1/nyc_sample_datasets/nycparking/parquet/' WITH PATTERN='*.parquet' AUTO_CREATE=TRUE TYPE=PARQUET"
   ```
   
   **💡 Basic Firebolt Core usage:**
   ```bash
   # Test connectivity
   docker exec firebolt-core fb -C -c "SELECT 'Hello Firebolt!' as message"
   
   # Check data loaded
   docker exec firebolt-core fb -C -c "SELECT COUNT(*) FROM violations"
   
   # Run a quick query
   docker exec firebolt-core fb -C -c "SELECT street_name, COUNT(*) FROM violations GROUP BY street_name LIMIT 5"
   ```

4. **Start the Streamlit app (Terminal 2 - NEW TERMINAL):**
   
   **✅ CONFIRMED: You DO need a new terminal for the Streamlit app**
   
   **Why a new terminal is required:**
   - The first terminal is needed to keep Firebolt Core running and accessible
   - The virtual environment state is maintained per terminal session
   - Streamlit runs as a long-running process that blocks the terminal
   
   ```bash
   # Navigate to project directory (replace with your actual path)
   cd /path/to/firebolt-nyc-demo
   
   # Activate virtual environment
   source .venv/bin/activate        # Linux/Mac
   # OR on Windows:
   # .venv\Scripts\activate
   
   # Verify activation (should show venv path)
   which python
   
   # Start the Streamlit app
   streamlit run app/streamlit_app.py
   ```
   
   **💡 Virtual Environment Notes:**
   - The `(.venv)` prefix should appear in your terminal prompt when activated
   - If activation fails, recreate with: `rm -rf .venv && python3 -m venv .venv`
   - Always activate the venv before running Streamlit manually

5. **Open your browser:** http://localhost:8501

## 📊 Dataset

**NYC Parking Violations 2019-2023**
- **Source:** Firebolt sample datasets (S3)
- **Size:** ~500MB compressed parquet files
- **Rows:** 2-5 million parking violations
- **Schema:** Issue date, location, vehicle info, fine amounts, violation codes

## 🏃 Benchmark Queries

| Query | Description | Performance Target |
|-------|-------------|--------------------|
| **Q1** | Total tickets & fines by fiscal year | < 100ms |
| **Q2** | Top 10 streets by revenue | < 200ms |
| **Q3** | 95th percentile fine by car make | < 300ms |
| **Q4** | Violations by hour of day | < 150ms |
| **Q5** | Interactive slice & dice filtering | < 250ms |

## 🚀 Why is Firebolt Core So Fast?

### Advanced Indexing
- **Sparse Indexes:** Accelerate time-based and location filtering
- **Aggregating Indexes:** Pre-computed rollups for instant analytics

### Engine Optimizations
- **Vectorized Processing:** SIMD-optimized computation
- **Columnar Storage:** Read only what you need
- **Advanced Query Optimizer:** Cost-based optimization with predicate pushdown

### Architecture
- **Distributed Query Engine:** Scale across multiple nodes
- **Memory-Optimized:** Efficient caching and memory management

## 📱 App Interface

### 🏃 Run Benchmarks Tab
- Execute all 5 benchmark queries with one click
- Real-time performance monitoring
- Query result visualization
- Execution time tracking

### 📊 Visualizations Tab
- **Trend Analysis:** Violations and fines over time
- **Geographic Insights:** Revenue by street/location
- **Temporal Patterns:** Peak violation hours
- **Vehicle Analytics:** Fine distributions by make

### 🧠 Why So Fast? Tab
- **Query Plan Comparison:** Before vs after indexes
- **Performance Explanations:** Technical deep-dive
- **Architecture Overview:** Engine capabilities

## 🛠️ Project Structure

```
firebolt-nyc-demo/
├── README.md                    # This file
├── setup_core.sh               # Firebolt Core bootstrap script
├── Makefile                    # Automation commands
├── requirements.txt            # Python dependencies
│
├── sql/                        # Database setup
│   ├── 01_create_tables.sql    # Table schema
│   ├── 02_load_data.sql        # Data loading from S3
│   └── 03_create_indexes.sql   # Performance indexes
│
├── app/
│   └── streamlit_app.py        # Main Streamlit application
│
├── scripts/
│   └── download_dataset.py     # Dataset preparation
│
└── data/                       # Local data cache (created)
    └── dataset_metadata.json   # Dataset information
```

## 🔧 Advanced Usage

### Multi-Node Deployment

```bash
# Create config for 3-node cluster
cat > config.json << EOF
{
    "nodes": [
        {"host": "node-0-ip"},
        {"host": "node-1-ip"}, 
        {"host": "node-2-ip"}
    ]
}
EOF

# Start cluster
docker compose up  # Node 0
NODE=1 docker compose -f compose.yaml -f compose.nodeN.yaml up  # Node 1
NODE=2 docker compose -f compose.yaml -f compose.nodeN.yaml up  # Node 2
```

### Custom Dataset

```python
# Use your own dataset
COPY INTO my_table FROM 's3://my-bucket/data/'
WITH PATTERN="*.parquet" AUTO_CREATE=TRUE TYPE=PARQUET;
```

### Query Customization

Edit `app/streamlit_app.py` to add your own benchmark queries:

```python
BENCHMARK_QUERIES["Q6"] = {
    "name": "My custom query",
    "sql": "SELECT ..."
}
```

## 📈 Performance Results

**Expected performance on 16GB laptop:**
- **Data loading:** < 5 minutes
- **Index creation:** < 2 minutes  
- **Query execution:** < 500ms average
- **UI responsiveness:** 30+ FPS

## 🐛 Troubleshooting

### Streamlit Cannot Connect to Firebolt Core

This is the most common issue. The Streamlit app provides detailed diagnostics, but here are manual steps:

```bash
# 1. Check if Docker is running
docker --version
docker ps

# 2. Check if Firebolt Core container exists and is running
docker ps | grep firebolt-core

# 3. If container doesn't exist, run setup
./setup_core.sh

# 4. If container exists but stopped, start it
docker start firebolt-core

# 5. Test direct connection
docker exec firebolt-core fb -C -c "SELECT 'Connection works!' as status"

# 6. Check container logs for errors
docker logs firebolt-core --tail 20
```

**💡 Common Causes:**
- Container not started: Run `./setup_core.sh`
- Wrong container name: Check with `docker ps -a`
- Permission issues: Ensure Docker daemon is running
- Memory limits: Firebolt Core needs 16GB+ RAM

### Firebolt Core Won't Start
```bash
# Check Docker resources
docker system df
docker system prune

# Check available memory
docker system info | grep Memory

# Restart with explicit memory settings
docker stop firebolt-core
docker rm firebolt-core
./setup_core.sh
```

### Data Loading Issues
```bash
# Check if data loading worked
docker exec firebolt-core fb -C -c "SELECT COUNT(*) FROM violations"

# If table doesn't exist, reload data - see manual data loading steps above

# Check for loading errors
docker logs firebolt-core | grep -i error
```

### Slow Query Performance
```bash
# Verify indexes exist
docker exec firebolt-core fb -C -c "SHOW INDEXES"

# Rebuild indexes if needed - see manual index creation steps above

# Check query execution plans
docker exec firebolt-core fb -C -c "EXPLAIN SELECT COUNT(*) FROM violations WHERE issue_date > '2022-01-01'"
```

### Python/Streamlit Issues
```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run Streamlit with verbose output
streamlit run app/streamlit_app.py --logger.level=debug
```

## 📚 Learn More

- [Firebolt Core Documentation](https://docs.firebolt.io/firebolt-core)
- [Firebolt SQL Reference](https://docs.firebolt.io/sql_reference/)
- [GitHub Repository](https://github.com/firebolt-db/firebolt-core)
- [Community Discord](https://discord.gg/UpMPDHActM)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Submit a pull request

## 📄 License

This demo is open source under the MIT License. See [LICENSE](LICENSE) for details.

---

**🚀 Ready to see Firebolt Core in action? Run `make all` and explore sub-second analytics!** 