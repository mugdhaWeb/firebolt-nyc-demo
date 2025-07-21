# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Core Setup and Management
```bash
# Initialize Firebolt Core (first time setup)
./setup_core.sh

# Load NYC parking data (run after setup_core.sh)
./load_data.sh

# Launch Streamlit dashboard
streamlit run app/streamlit_app.py
# Dashboard available at http://localhost:8501

# Check system status and connectivity
./check_status.sh

# Clean up containers and data
./cleanup.sh
```

### Code Quality and Testing
```bash
# Code formatting and linting
ruff check .
ruff format .
black .

# Type checking
mypy app/

# Run validation tests
python test_precache_validation.py
./test_validation_simple.sh
./validate_precaching.sh
```

### Database Access
```bash
# Direct SQL access via container
docker exec -it firebolt-core fb -C

# Example query
docker exec firebolt-core fb -C -c "SELECT COUNT(*) FROM violations;"
```

## Architecture Overview

This is a Firebolt Core demo showcasing sub-second analytics on 21.5M NYC parking violations. The application demonstrates high-performance analytical queries through containerized database deployment with intelligent caching.

### Key Components

**FireboltConnector (`app/streamlit_app.py:34-252`)**
- Manages database connections via Docker container execution
- Handles dual JSON/CSV output formats with robust parsing
- Executes queries through `docker exec firebolt-core fb -C` commands
- Provides comprehensive error handling and health checks

**Database Schema (`sql/01_create_tables.sql`)**
- Primary table: `violations` with 50+ columns including summons_number, plate_id, issue_date, vehicle_make, street_name, fine_amount
- Calculated fields added during load (calculated_fine_amount)
- Optimized for analytical workloads with proper data types

**Performance Strategy**
- **Pre-caching**: All queries silently executed during data load for guaranteed sub-200ms performance
- **Sparse indexes**: Created on issue_date, street_name, vehicle_make, violation_code
- **Aggregating indexes**: Pre-computed daily/hourly stats, street statistics, vehicle analysis
- **Streamlit caching**: `@st.cache_data` with TTL for filter data

### Data Pipeline Flow

1. **Container Setup**: `setup_core.sh` initializes Firebolt Core container
2. **Data Loading**: `load_data.sh` ingests S3 parquet files (~500MB compressed)
3. **Schema Enhancement**: Business logic applied to calculate fine amounts
4. **Index Creation**: Sparse and aggregating indexes for query optimization
5. **Cache Warming**: Silent execution of all 9 analytical queries (5 main + 4 filter)
6. **Validation**: Comprehensive testing ensures all queries return >0 rows

### Dashboard Structure

**Three-tab Streamlit Interface:**
- **Run Benchmarks**: Execute 5 analytical queries with real-time timing
- **Visualizations**: Auto-generated Plotly charts based on query results
- **Browse Data**: Sample data exploration and dataset statistics

**Dynamic Filtering:**
- Street name (dropdown selection)
- Vehicle make (dropdown selection) 
- Fine amount range (slider)
- All filters dynamically applied to queries

### Analytical Queries

**Q1**: Aggregation statistics (COUNT, SUM, AVG, MIN, MAX of violations and fines)
**Q2**: Revenue by street (GROUP BY street_name with sorting)
**Q3**: Vehicle make analysis (Multi-column aggregations by vehicle_make)
**Q4**: Time series analysis (EXTRACT year from issue_date with grouping)
**Q5**: Interactive filtering with violation categorization (CASE statements)

### Development Notes

- All Python dependencies managed via `requirements.txt` (Streamlit, Plotly, Pandas, NumPy, Requests)
- Code quality enforced via Ruff (line length 88, extensive rule set)
- Type checking configured for Python 3.11+ with mypy
- Docker required with minimum 16GB RAM allocation
- Query validation ensures data integrity with exit code 99 on failures

### Key Files

- `app/streamlit_app.py`: Main Streamlit application (500+ lines)
- `sql/*.sql`: Database schema, data loading, index creation
- `scripts/download_dataset.py`: Dataset retrieval utilities  
- `test_*.py/*.sh`: Validation and testing scripts
- `docker-compose.yml`: Container orchestration
- `pyproject.toml`: Python project configuration with Ruff/Black/mypy settings