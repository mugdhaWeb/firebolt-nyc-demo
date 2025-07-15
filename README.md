# 🚗 Firebolt Core NYC Parking Demo

**Analyze 21.5+ million NYC parking violations with lightning-fast sub-second queries!**

This demo showcases [Firebolt Core's](https://github.com/firebolt-db/firebolt-core) high-performance distributed query engine using real NYC parking violations data. Experience blazing-fast analytics on massive datasets with an interactive Streamlit interface.

## ✨ What You'll Get

- 🚀 **Sub-second queries** on 21.5M+ rows of real data
- 📊 **Interactive visualizations** with real-time filtering
- 🏃 **Live benchmarking** with performance monitoring
- 🎯 **5 analytical workloads** showcasing different query patterns
- 📈 **Advanced filtering** by street, vehicle make, and fine amount

## 🎯 Quick Start (10 Minutes)

**Prerequisites:**
- Docker Engine (16GB+ RAM recommended)
- Python 3.11+
- macOS, Linux, or Windows with WSL2

### Step 1: Setup Firebolt Core (2 minutes)

```bash
# Move to proper directory
cd firebolt-nyc-demo

# Make setup scripts executable
chmod +x setup_core.sh load_data.sh check_status.sh cleanup.sh

# Start Firebolt Core database
./setup_core.sh
```

**✅ Wait for**: "Firebolt Core is ready!" message

### Step 2: Setup Python Environment (2 minutes)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Load Data (3 minutes)

```bash
# Load 21.5M NYC parking violations from S3
./load_data.sh
```

**✅ Wait for**: "Data loading completed successfully!"

### Step 4: Launch Streamlit (1 minute)

```bash
# Start the web interface
streamlit run app/streamlit_app.py
```

**✅ Open**: http://localhost:8501

## 🚀 You're Ready!

Your system now has:
- **21,563,502 NYC parking violations** loaded and indexed
- **Sub-second query performance** on massive datasets
- **Interactive web interface** for exploration and benchmarking

## 📊 What You Can Do

### 🏃 Run Benchmarks
Execute all 5 benchmark queries and see performance metrics:
- **Q1**: Fiscal year aggregation (~50ms)
- **Q2**: Top streets by revenue (~150ms)
- **Q3**: Vehicle make fine analysis (~300ms)
- **Q4**: Hourly violation patterns (~120ms)
- **Q5**: Interactive filtering (~250ms)

### 📈 Explore Data
- **Filter by Street**: Choose from 11,000+ NYC streets
- **Filter by Vehicle**: Honda, Toyota, Ford, BMW, and more
- **Filter by Fine Amount**: $0-$200 range slider
- **Real-time Results**: All filters work together instantly

### 🔍 Browse Raw Data
- View latest violations in real-time
- Explore dataset metadata and statistics
- Understand data quality and coverage

## 🔧 Helper Scripts

### Check System Status
```bash
./check_status.sh
```
Verifies that Firebolt Core is running, data is loaded, and Python environment is ready.

### Clean Up Everything
```bash
./cleanup.sh
```
Removes all containers, data, and virtual environment for a fresh start.

### Reload Data
```bash
./load_data.sh
```
Drops and reloads the violations table with fresh data from S3.



## 🐛 Troubleshooting

### "Firebolt Core is not running"
```bash
# Check container status
docker ps | grep firebolt-core

# If not running, restart
./setup_core.sh
```

### "relation violations does not exist"
```bash
# Load the data
./load_data.sh

# Or check if container has persistent data
docker exec firebolt-core fb -C -c "SHOW TABLES"
```

### "Port 8501 is already in use"
```bash
# Find and kill the process
lsof -ti:8501 | xargs kill -9

# Or use a different port
streamlit run app/streamlit_app.py --server.port=8502
```

### Virtual Environment Issues
```bash
# Remove and recreate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Complete Reset
```bash
# Clean everything and start over
./cleanup.sh

# Then follow the setup steps again
./setup_core.sh
# ... etc
```

## 🔍 Advanced Usage

### Query the Database Directly
```bash
# Interactive SQL shell
docker exec -it firebolt-core fb -C

# Single query
docker exec firebolt-core fb -C -c "SELECT COUNT(*) FROM violations"
```

### Performance Monitoring
```bash
# Check query performance
docker exec firebolt-core fb -C -c "
SELECT
    COUNT(*) as total_violations,
    AVG(calculated_fine_amount) as avg_fine,
    COUNT(DISTINCT street_name) as unique_streets
FROM violations"
```

### Export Data
```bash
# Export to CSV
docker exec firebolt-core fb -C -c "
SELECT * FROM violations
WHERE issue_date >= '2023-01-01'
LIMIT 1000" -f CSV > sample_data.csv
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your improvements
4. Test with `./check_status.sh`
5. Submit a pull request

## 📚 Learn More

- [Firebolt Core Documentation](https://docs.firebolt.io/firebolt-core)
- [Firebolt SQL Reference](https://docs.firebolt.io/sql_reference/)
- [GitHub Repository](https://github.com/firebolt-db/firebolt-core)
- [Community Discord](https://discord.gg/UpMPDHActM)
