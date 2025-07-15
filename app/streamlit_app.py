#!/usr/bin/env python3
"""
Firebolt Core NYC Parking Violations Demo App

This Streamlit app demonstrates the power of Firebolt Core with:
- Real-time query execution and timing
- Interactive visualizations
- Performance analysis and explanations
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
import subprocess
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Firebolt Core NYC Demo",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

class FireboltConnector:
    """Handles connection and queries to Firebolt Core."""
    
    def __init__(self):
        self.container_name = "firebolt-core"
        self._check_docker_setup()
    
    def _check_docker_setup(self):
        """Check if Docker and Firebolt Core container are available."""
        try:
            # Check if Docker is available
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Docker is not available or not running")
                return False
            
            # Check if container exists
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True, text=True
            )
            
            if self.container_name not in result.stdout:
                logger.error(f"Container '{self.container_name}' not found")
                return False
            
            # Check if container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True, text=True
            )
            
            if self.container_name not in result.stdout:
                logger.warning(f"Container '{self.container_name}' exists but is not running")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Docker setup check failed: {e}")
            return False
    
    def execute_query(self, query: str, timeout: int = 60) -> Tuple[pd.DataFrame, float, bool]:
        """
        Execute a query and return results with timing.
        Returns: (dataframe, execution_time_seconds, success)
        """
        start_time = time.time()
        
        try:
            # Use docker exec to run fb with Firebolt Core settings
            cmd = [
                "docker", "exec", self.container_name, 
                "fb", "-C", "-c", query, "-f", "JSONLines_Compact"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                # Parse JSON output
                if result.stdout.strip():
                    df = self._parse_jsonlines_output(result.stdout)
                    return df, execution_time, True
                else:
                    return pd.DataFrame(), execution_time, True
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"Query failed: {error_msg}")
                return pd.DataFrame(), execution_time, False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Query timed out after {timeout} seconds")
            return pd.DataFrame(), timeout, False
        except FileNotFoundError:
            logger.error("Docker command not found. Is Docker installed and in PATH?")
            execution_time = time.time() - start_time
            return pd.DataFrame(), execution_time, False
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            execution_time = time.time() - start_time
            return pd.DataFrame(), execution_time, False
    
    def _parse_jsonlines_output(self, output: str) -> pd.DataFrame:
        """Parse JSONLines output from Firebolt Core into a pandas DataFrame."""
        import json
        import re
        
        # Clean output by removing terminal control characters and progress indicators
        cleaned_output = re.sub(r'[^\x20-\x7E\n\r\t]', '', output)
        
        # Split output into lines and rejoin JSON objects that may be split across lines
        lines = cleaned_output.strip().split('\n')
        
        # Filter and reconstruct JSON lines
        json_lines = []
        current_json = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip timing and metadata lines
            if line.startswith('Time:') or line.startswith('Request Id:'):
                continue
            
            # Check if this looks like JSON
            if line.startswith('{'):
                # Start of a new JSON object
                if current_json:
                    json_lines.append(current_json)
                current_json = line
            else:
                # Continuation of current JSON object
                current_json += line
            
            # Check if we have a complete JSON object
            if current_json and current_json.endswith('}'):
                json_lines.append(current_json)
                current_json = ""
        
        # Add any remaining JSON
        if current_json:
            json_lines.append(current_json)
        
        columns = []
        data_rows = []
        
        for json_line in json_lines:
            try:
                msg = json.loads(json_line)
                
                if msg.get('message_type') == 'START':
                    # Extract column names from START message
                    result_columns = msg.get('result_columns', [])
                    columns = [col['name'] for col in result_columns]
                    
                elif msg.get('message_type') == 'DATA':
                    # Extract data rows from DATA message
                    data = msg.get('data', [])
                    data_rows.extend(data)
                    
            except json.JSONDecodeError:
                # Skip invalid JSON
                continue
        
        # Create DataFrame
        if columns and data_rows:
            df = pd.DataFrame(data_rows)
            df.columns = columns
            return df
        else:
            return pd.DataFrame()
    
    def test_connection(self) -> bool:
        """Test if Firebolt Core is accessible."""
        _, _, success = self.execute_query("SELECT 1 as test", timeout=10)
        return success
    
    def get_diagnostics(self) -> str:
        """Get diagnostic information for troubleshooting."""
        diagnostics = []
        
        try:
            # Check Docker status
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                diagnostics.append(f"✅ Docker: {result.stdout.strip()}")
            else:
                diagnostics.append("❌ Docker: Not available")
            
            # Check container status
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={self.container_name}", 
                 "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
                capture_output=True, text=True
            )
            
            if result.stdout.strip():
                diagnostics.append(f"📋 Container Status:\n{result.stdout}")
            else:
                diagnostics.append(f"❌ Container '{self.container_name}' not found")
            
            # Check container logs (last 10 lines)
            result = subprocess.run(
                ["docker", "logs", "--tail", "10", self.container_name],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                diagnostics.append(f"📄 Recent logs:\n{result.stdout}")
            else:
                diagnostics.append("❌ Cannot access container logs")
                
        except Exception as e:
            diagnostics.append(f"❌ Diagnostic error: {e}")
        
        return "\n\n".join(diagnostics)

# Initialize Firebolt connector
@st.cache_resource
def get_firebolt_connector():
    return FireboltConnector()

def get_available_streets(connector: FireboltConnector) -> List[str]:
    """Get list of available street names from the database."""
    try:
        df, _, success = connector.execute_query("SELECT DISTINCT street_name FROM violations WHERE street_name IS NOT NULL ORDER BY street_name LIMIT 1000")
        if success and not df.empty:
            return df['street_name'].tolist()
    except Exception as e:
        logger.error(f"Error fetching streets: {e}")
    return []

def get_available_amounts(connector: FireboltConnector) -> List[float]:
    """Get list of available fine amounts from the database."""
    try:
        df, _, success = connector.execute_query("SELECT DISTINCT calculated_fine_amount FROM violations WHERE calculated_fine_amount IS NOT NULL ORDER BY calculated_fine_amount LIMIT 1000")
        if success and not df.empty:
            return df['calculated_fine_amount'].tolist()
    except Exception as e:
        logger.error(f"Error fetching amounts: {e}")
    return []

def get_available_cars(connector: FireboltConnector) -> List[str]:
    """Get list of available vehicle makes from the database."""
    try:
        df, _, success = connector.execute_query("""
            SELECT vehicle_make
            FROM violations 
            WHERE vehicle_make IS NOT NULL 
                AND LENGTH(vehicle_make) >= 3
                AND vehicle_make != ''
            GROUP BY vehicle_make
            HAVING COUNT(*) >= 1000
            ORDER BY COUNT(*) DESC
            LIMIT 50
        """)
        if success and not df.empty:
            return df['vehicle_make'].tolist()
    except Exception as e:
        logger.error(f"Error fetching cars: {e}")
    return []

def show_data_browser(connector: FireboltConnector):
    """Display the current data in the violations table."""
    try:
        df, exec_time, success = connector.execute_query("SELECT summons_number, plate_id, registration_state, issue_date, vehicle_make, street_name, calculated_fine_amount FROM violations ORDER BY issue_date DESC LIMIT 100")
        
        if success and not df.empty:
            st.dataframe(df, use_container_width=True)
            
            # Show statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Violations", "21,563,502")
            with col2:
                st.metric("Unique Streets", int(df['street_name'].nunique()))
            with col3:
                st.metric("Average Fine", f"${float(df['calculated_fine_amount'].mean()):.2f}")
                
            st.caption(f"Query executed in {exec_time*1000:.1f}ms (showing latest 100 records)")
        else:
            st.info("No data found in the violations table")
    except Exception as e:
        st.error(f"Error loading data: {e}")



# Benchmark queries - updated for violations table
BENCHMARK_QUERIES = {
    "Q1": {
        "name": "Total violations & fines summary",
        "description": "Overall statistics from the NYC dataset",
        "sql": """
            SELECT 
                COUNT(*) as total_violations,
                SUM(calculated_fine_amount) as total_fines,
                AVG(calculated_fine_amount) as avg_fine,
                MIN(calculated_fine_amount) as min_fine,
                MAX(calculated_fine_amount) as max_fine
            FROM violations 
            WHERE calculated_fine_amount > 0
        """
    },
    "Q2": {
        "name": "Revenue by street",
        "description": "Top 10 streets by revenue",
        "sql": """
            SELECT 
                street_name,
                COUNT(*) as total_violations,
                SUM(calculated_fine_amount) as total_revenue,
                AVG(calculated_fine_amount) as avg_fine
            FROM violations 
            WHERE street_name IS NOT NULL 
                AND street_name != ''
                AND calculated_fine_amount > 0
            GROUP BY street_name
            ORDER BY total_revenue DESC
            LIMIT 10
        """
    },
    "Q3": {
        "name": "Vehicle make analysis",
        "description": "Violations by vehicle make",
        "sql": """
            SELECT 
                vehicle_make,
                COUNT(*) as violations,
                AVG(calculated_fine_amount) as avg_fine,
                SUM(calculated_fine_amount) as total_fines
            FROM violations 
            WHERE vehicle_make IS NOT NULL 
                AND calculated_fine_amount > 0
            GROUP BY vehicle_make
            ORDER BY violations DESC
            LIMIT 10
        """
    },
    "Q4": {
        "name": "Yearly trend analysis",
        "description": "Violations by year",
        "sql": """
            SELECT 
                EXTRACT(YEAR FROM issue_date) as year,
                COUNT(*) as violation_count,
                SUM(calculated_fine_amount) as total_revenue,
                AVG(calculated_fine_amount) as avg_fine
            FROM violations 
            WHERE issue_date IS NOT NULL 
                AND calculated_fine_amount > 0
                AND EXTRACT(YEAR FROM issue_date) BETWEEN 2010 AND 2024
            GROUP BY EXTRACT(YEAR FROM issue_date)
            ORDER BY year
        """
    },
    "Q5": {
        "name": "Interactive data filtering",
        "description": "Filter violations by street name, fine amount, and vehicle make",
        "sql": """
            SELECT 
                summons_number,
                street_name,
                calculated_fine_amount,
                issue_date,
                vehicle_make,
                CASE 
                    WHEN calculated_fine_amount > 100 THEN 'High Fine'
                    WHEN calculated_fine_amount > 50 THEN 'Medium Fine'
                    ELSE 'Low Fine'
                END as fine_category
            FROM violations 
            WHERE calculated_fine_amount > 0
                {street_filter}
                {amount_filter}
                {car_filter}
            ORDER BY calculated_fine_amount DESC
            LIMIT 100
        """
    }
}

def main():
    """Main Streamlit app."""
    
    # App header
    st.title("🚗 Firebolt Core NYC Parking Demo")
    st.markdown("""
    **Explore 21.5+ million NYC parking violations with sub-second analytics!**
    
    This demo showcases Firebolt Core's high-performance query engine with real NYC open data loaded from S3.
    The dataset contains actual NYC parking violations from 1972-2024.
    """)
    
    # Initialize session state
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'query_results' not in st.session_state:
        st.session_state.query_results = {}
    
    # Connection status
    connector = get_firebolt_connector()
    
    if connector.test_connection():
        st.sidebar.success("✅ Connected to Firebolt Core")
        
        # Sidebar filters (only show if connected)
        st.sidebar.header("🎛️ Query Filters")
        
        # Get available data for filters
        available_streets = get_available_streets(connector)
        available_amounts = get_available_amounts(connector)
        available_cars = get_available_cars(connector)
        
        # Street filter with selectbox
        street_options = ["All Streets"] + available_streets
        selected_street = st.sidebar.selectbox(
            "Street Name", 
            options=street_options,
            help="Select a street to filter violations",
            key="street_filter"
        )
        street_filter = selected_street if selected_street != "All Streets" else ""
        
        # Car filter with selectbox
        car_options = ["All Cars"] + available_cars
        selected_car = st.sidebar.selectbox(
            "Vehicle Make", 
            options=car_options,
            help="Select a vehicle make to filter violations",
            key="car_filter"
        )
        car_filter = selected_car if selected_car != "All Cars" else ""
        
        # Fine amount filter
        if available_amounts:
            min_amount = min(available_amounts)
            max_amount = max(available_amounts)
            amount_range = st.sidebar.slider(
                "Fine Amount Range", 
                min_value=float(min_amount),
                max_value=float(max_amount),
                value=(float(min_amount), float(max_amount)),
                help="Filter violations by fine amount",
                key="amount_filter"
            )
        else:
            amount_range = (0.0, 200.0)
        
        # Filter summary and reset button
        active_filters = []
        if street_filter:
            active_filters.append(f"Street: {street_filter}")
        if car_filter:
            active_filters.append(f"Car: {car_filter}")
        if amount_range != (min(available_amounts) if available_amounts else 0.0, max(available_amounts) if available_amounts else 200.0):
            active_filters.append(f"Amount: ${amount_range[0]:.0f}-${amount_range[1]:.0f}")
        
        if active_filters:
            st.sidebar.info(f"🔍 Active filters: {', '.join(active_filters)}")
        
        if st.sidebar.button("🔄 Reset Filters"):
            st.rerun()
        
        # Auto-refresh filtered query when filters change
        if st.sidebar.button("🚀 Apply Filters (Run Q5)", type="primary"):
            execute_benchmark_query("Q5", BENCHMARK_QUERIES["Q5"], connector, 
                                  street_filter, amount_range, car_filter)
            
        # Quick filter test
        if active_filters and st.sidebar.button("🔍 Quick Filter Test", help="Test filters with a quick count"):
            with st.spinner("Testing filters..."):
                filter_clauses = []
                if street_filter:
                    filter_clauses.append(f"street_name = '{street_filter}'")
                if car_filter:
                    filter_clauses.append(f"vehicle_make = '{car_filter}'")
                filter_clauses.append(f"calculated_fine_amount BETWEEN {amount_range[0]} AND {amount_range[1]}")
                
                where_clause = " AND ".join(filter_clauses)
                test_query = f"SELECT COUNT(*) as filtered_count FROM violations WHERE {where_clause}"
                
                result_df, exec_time, success = connector.execute_query(test_query)
                if success and not result_df.empty:
                    count = result_df.iloc[0]['filtered_count']
                    st.sidebar.success(f"✅ Found {count:,} matching violations in {exec_time*1000:.1f}ms")
                else:
                    st.sidebar.error("❌ Filter test failed")
        
    else:
        st.sidebar.error("❌ Cannot connect to Firebolt Core")
        
        # Show detailed diagnostics
        with st.expander("🔍 Connection Diagnostics", expanded=True):
            st.text(connector.get_diagnostics())
            
            st.markdown("""
            ### Troubleshooting Steps:
            
            1. **Ensure Firebolt Core is running:**
               ```bash
               ./setup_core.sh
               ```
            
            2. **Check container status:**
               ```bash
               docker ps | grep firebolt-core
               ```
            
            3. **Test direct connection:**
               ```bash
               docker exec firebolt-core fb -C -c "SELECT 1"
               ```
            
            4. **Restart if needed:**
               ```bash
               docker stop firebolt-core
               docker rm firebolt-core
               ./setup_core.sh
               ```
            """)
        
        # Set default values if not connected
        street_filter = ""
        car_filter = ""
        amount_range = (0.0, 200.0)
        active_filters = []
        
        st.stop()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏃 Run Benchmarks", "📊 Visualizations", "🔍 Browse Data", "🧠 Why So Fast?"])
    
    with tab1:
        st.header("Benchmark Queries")
        st.markdown("Click any button to execute queries and see sub-second performance!")
        
        # Show current filter settings
        if active_filters:
            with st.expander("🔍 Current Filter Settings", expanded=True):
                st.markdown("**Active Filters:**")
                if street_filter:
                    st.markdown(f"- **Street Name:** {street_filter}")
                if car_filter:
                    st.markdown(f"- **Vehicle Make:** {car_filter}")
                st.markdown(f"- **Fine Amount Range:** ${amount_range[0]:.0f} - ${amount_range[1]:.0f}")
                st.info("💡 Use **Q5: Interactive data filtering** to see filtered results!")
        
        # Create columns for benchmark buttons
        cols = st.columns(3)
        
        # Query execution buttons
        for i, (query_id, query_info) in enumerate(BENCHMARK_QUERIES.items()):
            col_idx = i % 3
            
            with cols[col_idx]:
                if st.button(f"{query_id}: {query_info['name']}", key=f"btn_{query_id}"):
                    execute_benchmark_query(query_id, query_info, connector, 
                                          street_filter, amount_range, car_filter)
        
        # Display results table
        if st.session_state.query_results:
            st.subheader("📈 Execution Results")
            
            results_data = []
            for query_id, result in st.session_state.query_results.items():
                results_data.append({
                    "Query": query_id,
                    "Description": BENCHMARK_QUERIES[query_id]["name"],
                    "Execution Time (ms)": f"{result['execution_time']*1000:.1f}",
                    "Rows Returned": result['row_count'],
                    "Status": "✅ Success" if result['success'] else "❌ Failed"
                })
            
            results_df = pd.DataFrame(results_data)
            st.dataframe(results_df, use_container_width=True)
            
            # Show latest query result
            if results_data:
                latest_query = list(st.session_state.query_results.keys())[-1]
                latest_result = st.session_state.query_results[latest_query]
                
                st.subheader(f"Latest Query Results: {latest_query}")
                if not latest_result['data'].empty:
                    st.dataframe(latest_result['data'], use_container_width=True)
    
    with tab2:
        st.header("Data Visualizations")
        
        if not st.session_state.query_results:
            st.info("🚀 Run some benchmark queries first to see visualizations!")
            st.markdown("""
            **Available Visualizations:**
            - **Q1**: Overall statistics with key metrics
            - **Q2**: Revenue breakdown by street with bar charts
            - **Q3**: Vehicle make analysis with violation counts
            - **Q4**: Yearly trend analysis with time series
            - **Q5**: Interactive filtered results with scatter plots
            
            Click the benchmark query buttons in the **Run Benchmarks** tab to generate data for visualizations.
            """)
        else:
            # Show summary of available results
            st.markdown(f"**Available Results:** {', '.join(st.session_state.query_results.keys())}")
            
            # Create visualizations for all available results
            create_visualizations()
    
    with tab3:
        st.header("Browse Data")
        
        # Show current data in the table
        st.subheader("🔍 Current Data in violations Table")
        
        if st.button("🔄 Refresh Data", help="Reload data from the database"):
            show_data_browser(connector)
        
        # Show initial data
        show_data_browser(connector)
        
        # Data information section
        st.subheader("📊 Dataset Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Dataset Details:**")
            st.info("""
            - **Source**: NYC Open Data via Firebolt Sample Datasets
            - **Total Records**: 21,563,502 violations
            - **Date Range**: 1972-2024 (with data quality issues)
            - **Size**: ~500MB compressed parquet files
            - **Location**: S3 bucket (public access)
            """)
        
        with col2:
            st.markdown("**Quick Stats:**")
            if st.button("📈 Run Quick Stats", type="secondary"):
                with st.spinner("Calculating statistics..."):
                    stats_df, exec_time, success = connector.execute_query("""
                        SELECT 
                            COUNT(*) as total_violations,
                            COUNT(DISTINCT street_name) as unique_streets,
                            COUNT(DISTINCT vehicle_make) as unique_makes,
                            AVG(calculated_fine_amount) as avg_fine
                        FROM violations 
                        WHERE calculated_fine_amount > 0
                    """)
                    if success and not stats_df.empty:
                        st.success(f"Stats calculated in {exec_time*1000:.1f}ms")
                        st.dataframe(stats_df, use_container_width=True)
                    else:
                        st.error("Failed to calculate statistics")
    
    with tab4:
        st.header("Why is Firebolt Core So Fast?")
        
        with st.expander("🔍 Query Execution Plans", expanded=True):
            explain_performance(connector)
        
        with st.expander("🚀 Performance Features", expanded=True):
            st.markdown("""
            ### Firebolt Core's Speed Secrets:
            
            1. **🎯 Sparse Indexes**: Smart indexing on frequently-filtered columns
               - Issue date index accelerates time-based queries
               - Street name index speeds up location filtering
            
            2. **📊 Aggregating Indexes**: Pre-computed aggregations
               - Daily statistics calculated once, queried instantly  
               - Hourly patterns materialized for real-time analysis
            
            3. **⚡ Vectorized Engine**: SIMD-optimized processing
               - Process multiple rows simultaneously
               - Efficient memory utilization
            
            4. **🗜️ Columnar Storage**: Optimized data layout
               - Only read columns you need
               - Better compression ratios
            
            5. **🔧 Advanced Query Optimizer**: 
               - Cost-based optimization
               - Predicate pushdown
               - Join reordering
            """)

def execute_benchmark_query(query_id: str, query_info: Dict, connector: FireboltConnector, 
                          street_filter: str, amount_range: tuple, car_filter: str = ""):
    """Execute a benchmark query with timing."""
    
    with st.spinner(f"Executing {query_id}..."):
        # Prepare query with filters for Q5
        sql = query_info["sql"]
        if query_id == "Q5":
            street_clause = f"AND street_name = '{street_filter}'" if street_filter else ""
            amount_clause = f"AND calculated_fine_amount BETWEEN {amount_range[0]} AND {amount_range[1]}"
            car_clause = f"AND vehicle_make = '{car_filter}'" if car_filter else ""
            
            sql = sql.format(
                street_filter=street_clause,
                amount_filter=amount_clause,
                car_filter=car_clause
            )
        
        # Execute query
        result_df, execution_time, success = connector.execute_query(sql)
        
        # Store results
        st.session_state.query_results[query_id] = {
            'data': result_df,
            'execution_time': execution_time,
            'row_count': len(result_df) if success else 0,
            'success': success,
            'timestamp': datetime.now()
        }
        
        if success:
            st.success(f"✅ {query_id} completed in {execution_time*1000:.1f}ms")
        else:
            st.error(f"❌ {query_id} failed")

def create_visualizations():
    """Create visualizations from query results."""
    
    visualizations_shown = 0
    
    # Overall statistics (Q1)
    if "Q1" in st.session_state.query_results:
        q1_data = st.session_state.query_results["Q1"]["data"]
        if not q1_data.empty and len(q1_data) > 0:
            st.subheader("📊 Overall Statistics")
            
            # Show metrics as cards with null checks
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                violations = q1_data.iloc[0]['total_violations']
                st.metric("Total Violations", f"{int(violations):,}" if violations is not None else "N/A")
            with col2:
                fines = q1_data.iloc[0]['total_fines']
                st.metric("Total Fines", f"${float(fines):,.2f}" if fines is not None else "N/A")
            with col3:
                avg_fine = q1_data.iloc[0]['avg_fine']
                st.metric("Average Fine", f"${float(avg_fine):.2f}" if avg_fine is not None else "N/A")
            with col4:
                min_fine = q1_data.iloc[0]['min_fine']
                max_fine = q1_data.iloc[0]['max_fine']
                if min_fine is not None and max_fine is not None:
                    st.metric("Fine Range", f"${float(min_fine):.0f} - ${float(max_fine):.0f}")
                else:
                    st.metric("Fine Range", "N/A")
            
            visualizations_shown += 1
    
    # Street revenue breakdown (Q2)
    if "Q2" in st.session_state.query_results:
        q2_data = st.session_state.query_results["Q2"]["data"]
        if not q2_data.empty and len(q2_data) > 0:
            st.subheader("💰 Revenue by Street")
            
            # Create bar chart
            fig = px.bar(
                q2_data, 
                x='street_name', 
                y='total_revenue',
                color='avg_fine',
                title="Total Revenue by Street",
                labels={'total_revenue': 'Total Revenue ($)', 'street_name': 'Street Name', 'avg_fine': 'Avg Fine ($)'},
                color_continuous_scale='viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show data table
            st.dataframe(q2_data, use_container_width=True)
            
            visualizations_shown += 1
    
    # Vehicle make analysis (Q3)
    if "Q3" in st.session_state.query_results:
        q3_data = st.session_state.query_results["Q3"]["data"]
        if not q3_data.empty and len(q3_data) > 0:
            st.subheader("📈 Vehicle Make Analysis")
            
            fig = px.bar(
                q3_data,
                x='vehicle_make',
                y='avg_fine',
                color='violations',
                title="Average Fine by Vehicle Make",
                labels={'vehicle_make': 'Vehicle Make', 'avg_fine': 'Average Fine ($)', 'violations': 'Number of Violations'}
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show data table
            st.dataframe(q3_data, use_container_width=True)
            
            visualizations_shown += 1
    
    # Yearly trend analysis (Q4)
    if "Q4" in st.session_state.query_results:
        q4_data = st.session_state.query_results["Q4"]["data"]
        if not q4_data.empty and len(q4_data) > 0:
            st.subheader("📅 Yearly Trend Analysis")
            
            # Create line chart for trends
            fig = px.line(
                q4_data,
                x='year',
                y='violation_count',
                title="Violations Over Time",
                labels={'year': 'Year', 'violation_count': 'Number of Violations'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show data table
            st.dataframe(q4_data, use_container_width=True)
            
            visualizations_shown += 1
    
    # Interactive filtering (Q5)
    if "Q5" in st.session_state.query_results:
        q5_data = st.session_state.query_results["Q5"]["data"]
        if not q5_data.empty and len(q5_data) > 0:
            st.subheader("🔍 Filtered Results")
            
            # Create scatter plot
            fig = px.scatter(
                q5_data,
                x='calculated_fine_amount',
                y='issue_date',
                color='fine_category',
                hover_data=['street_name', 'vehicle_make'],
                title="Filtered Violations",
                labels={'calculated_fine_amount': 'Fine Amount ($)', 'issue_date': 'Issue Date'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show data table
            st.dataframe(q5_data, use_container_width=True)
            
            visualizations_shown += 1
    
    # Fallback message if no visualizations were shown
    if visualizations_shown == 0:
        st.warning("⚠️ No visualizations available. This might happen if:")
        st.markdown("""
        - Query results are empty or failed
        - Data contains only null values
        - There was an error processing the query results
        
        Try running the benchmark queries again or check the connection status.
        """)

def explain_performance(connector: FireboltConnector):
    """Show query execution plans and performance explanations."""
    
    st.markdown("### Query Performance Analysis")
    
    sample_query = """
    SELECT COUNT(*), SUM(calculated_fine_amount) 
    FROM violations 
    WHERE street_name = 'Broadway'
    """
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Current Query Plan")
        if st.button("Show Execution Plan"):
            explain_query = f"EXPLAIN {sample_query}"
            result_df, exec_time, success = connector.execute_query(explain_query)
            
            if success and not result_df.empty:
                st.text(str(result_df.iloc[0, 0]) if len(result_df.columns) > 0 else "No plan available")
            else:
                st.text("Query plan not available")
    
    with col2:
        st.subheader("⚡ Performance Tips")
        st.markdown("""
        **For Production Workloads:**
        
        - **Sparse Indexes**: Create indexes on frequently filtered columns
        - **Primary Index**: Choose the right primary index column
        - **Aggregating Indexes**: Pre-compute common aggregations
        - **Partitioning**: Partition large tables by date/category
        
        **Current Test Table:**
        - Small dataset (< 10 rows)
        - Simple structure for demonstration
        - Perfect for testing queries
        """)
        
    # Show sample performance comparison
    st.markdown("### Performance Comparison")
    
    if st.button("Run Performance Test"):
        with st.spinner("Running performance test..."):
            # Test simple query
            start_time = time.time()
            df1, exec_time1, success1 = connector.execute_query("SELECT COUNT(*) FROM violations")
            
            # Test aggregation query
            df2, exec_time2, success2 = connector.execute_query("SELECT street_name, COUNT(*), AVG(calculated_fine_amount) FROM violations GROUP BY street_name LIMIT 10")
            
            if success1 and success2:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Count Query", f"{exec_time1*1000:.1f}ms")
                with col2:
                    st.metric("Aggregation Query", f"{exec_time2*1000:.1f}ms")
                
                st.success("✅ Queries executed successfully!")
            else:
                st.error("❌ Performance test failed")

if __name__ == "__main__":
    main() 