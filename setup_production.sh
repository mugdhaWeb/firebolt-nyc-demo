#!/bin/bash

set -e

echo "🚀 Firebolt Core NYC Demo - Production Setup"
echo "=============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker and try again."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11+ and try again."
        exit 1
    fi
    
    # Check available memory
    if command -v docker &> /dev/null; then
        memory_gb=$(docker system info 2>/dev/null | grep "Total Memory" | awk '{print $3}' | sed 's/GiB//')
        if [ -n "$memory_gb" ] && [ "$memory_gb" -lt 12 ]; then
            print_warning "Docker has less than 12GB memory allocated. This may cause data loading issues."
            print_warning "Consider increasing Docker memory to 16GB+ for optimal performance."
        fi
    fi
    
    print_success "Prerequisites check passed!"
}

# Function to setup Firebolt Core
setup_firebolt_core() {
    print_status "Setting up Firebolt Core..."
    
    # Make setup script executable
    chmod +x setup_core.sh
    
    # Run setup script
    if ./setup_core.sh; then
        print_success "Firebolt Core setup completed!"
    else
        print_error "Firebolt Core setup failed!"
        exit 1
    fi
    
    # Verify Firebolt Core is running
    print_status "Verifying Firebolt Core connectivity..."
    if docker exec firebolt-core fb -C -c "SELECT 'Connection verified!' as status" >/dev/null 2>&1; then
        print_success "Firebolt Core is running and accessible!"
    else
        print_error "Cannot connect to Firebolt Core!"
        exit 1
    fi
}

# Function to setup Python environment
setup_python_environment() {
    print_status "Setting up Python environment..."
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv .venv
    else
        print_status "Virtual environment already exists."
    fi
    
    # Activate virtual environment and install dependencies
    print_status "Installing Python dependencies..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Prepare dataset metadata
    print_status "Preparing dataset metadata..."
    python scripts/download_dataset.py
    
    print_success "Python environment setup completed!"
}

# Function to load production data
load_production_data() {
    print_status "Loading production data from S3..."
    
    # Create and run the data loading script
    if [ ! -f "load_production_data.sh" ]; then
        print_status "Creating data loading script..."
        cat > load_production_data.sh << 'EOF'
#!/bin/bash

set -e

echo "🔄 Loading NYC Parking Violations data from S3..."

# Check if Firebolt Core is running
if ! docker exec firebolt-core fb -C -c "SELECT 1" >/dev/null 2>&1; then
    echo "❌ Firebolt Core is not responding. Please run ./setup_core.sh first."
    exit 1
fi

# 1. Create the violations table
echo "📋 Creating violations table..."
docker exec firebolt-core fb -C -c "
DROP TABLE IF EXISTS violations;
CREATE TABLE violations (
    summons_number BIGINT,
    plate_id STRING,
    registration_state STRING,
    issue_date DATE,
    violation_code INT,
    vehicle_make STRING,
    street_name STRING,
    fine_amount DOUBLE
) PRIMARY INDEX summons_number"

# 2. Load data from S3
echo "📥 Loading data from S3 (this may take 2-5 minutes)..."
docker exec firebolt-core fb -C -c "
COPY INTO violations FROM 's3://firebolt-sample-datasets-public-us-east-1/nyc_sample_datasets/nycparking/parquet/'
WITH PATTERN='*.parquet' TYPE=PARQUET"

# 3. Add calculated fine amounts
echo "💰 Adding calculated fine amounts..."
docker exec firebolt-core fb -C -c "
ALTER TABLE violations ADD COLUMN calculated_fine_amount DOUBLE"

docker exec firebolt-core fb -C -c "
UPDATE violations SET calculated_fine_amount = 
CASE 
    WHEN violation_code = 36 THEN 65.0
    WHEN violation_code = 21 THEN 115.0
    WHEN violation_code = 38 THEN 35.0
    WHEN violation_code = 37 THEN 60.0
    WHEN violation_code = 20 THEN 95.0
    WHEN fine_amount > 0 THEN fine_amount
    ELSE 50.0
END"

# 4. Create performance indexes
echo "🎯 Creating performance indexes..."
docker exec firebolt-core fb -C -c "
CREATE INDEX idx_street ON violations (street_name);
CREATE INDEX idx_date ON violations (issue_date);
CREATE INDEX idx_make ON violations (vehicle_make);
CREATE INDEX idx_fine ON violations (calculated_fine_amount)"

# 5. Verify data
echo "✅ Verifying data loading..."
result=$(docker exec firebolt-core fb -C -c "
SELECT 
    COUNT(*) as total_violations,
    COUNT(DISTINCT street_name) as unique_streets,
    COUNT(DISTINCT vehicle_make) as unique_makes,
    ROUND(AVG(calculated_fine_amount), 2) as avg_fine,
    ROUND(SUM(calculated_fine_amount), 0) as total_revenue
FROM violations" -f JSONLines_Compact)

echo "📊 Data loading completed successfully!"
echo "Results: $result"

EOF
        chmod +x load_production_data.sh
    fi
    
    # Run the data loading script
    if ./load_production_data.sh; then
        print_success "Production data loaded successfully!"
    else
        print_error "Data loading failed!"
        exit 1
    fi
}

# Function to create diagnostics script
create_diagnostics_script() {
    print_status "Creating diagnostics script..."
    
    cat > diagnostics.sh << 'EOF'
#!/bin/bash

echo "🔍 Firebolt Core NYC Demo - System Diagnostics"
echo "=============================================="

# Check Docker
echo "📦 Docker Status:"
docker --version
docker info | grep -E "(Memory|CPUs|Operating System)"
echo ""

# Check containers
echo "🐳 Container Status:"
docker ps -a | grep -E "(firebolt|streamlit)" || echo "No Firebolt containers found"
echo ""

# Check Firebolt Core connectivity
echo "🔗 Firebolt Core Connectivity:"
if docker exec firebolt-core fb -C -c "SELECT 'OK' as status" 2>/dev/null; then
    echo "✅ Firebolt Core is responding"
else
    echo "❌ Firebolt Core is not responding"
fi
echo ""

# Check data
echo "📊 Data Status:"
if docker exec firebolt-core fb -C -c "SELECT COUNT(*) as row_count FROM violations" 2>/dev/null; then
    echo "✅ Data is loaded"
else
    echo "❌ No data found in violations table"
fi
echo ""

# Check Python environment
echo "🐍 Python Environment:"
if [ -d ".venv" ]; then
    echo "✅ Virtual environment exists"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        python --version
        pip show streamlit plotly pandas 2>/dev/null | grep -E "Name|Version" || echo "❌ Required packages not installed"
    fi
else
    echo "❌ Virtual environment not found"
fi
echo ""

# Check ports
echo "🌐 Port Status:"
if command -v lsof &> /dev/null; then
    lsof -i :3473 | grep LISTEN && echo "✅ Port 3473 (Firebolt Core) is open" || echo "❌ Port 3473 not in use"
    lsof -i :8501 | grep LISTEN && echo "✅ Port 8501 (Streamlit) is open" || echo "❌ Port 8501 not in use"
else
    echo "lsof not available - cannot check ports"
fi

echo ""
echo "🎯 Quick Fix Commands:"
echo "- Restart Firebolt Core: ./setup_core.sh"
echo "- Reload data: ./load_production_data.sh"
echo "- Start Streamlit: source .venv/bin/activate && streamlit run app/streamlit_app.py"

EOF
    chmod +x diagnostics.sh
    print_success "Diagnostics script created!"
}

# Function to validate installation
validate_installation() {
    print_status "Validating installation..."
    
    # Check Firebolt Core
    if ! docker exec firebolt-core fb -C -c "SELECT 1" >/dev/null 2>&1; then
        print_error "Firebolt Core validation failed!"
        return 1
    fi
    
    # Check data
    row_count=$(docker exec firebolt-core fb -C -c "SELECT COUNT(*) FROM violations" 2>/dev/null | tail -n1 | tr -d '[:space:]' || echo "0")
    if [ "$row_count" -gt 1000000 ]; then
        print_success "Data validation passed! ($row_count rows loaded)"
    else
        print_error "Data validation failed! Only $row_count rows found"
        return 1
    fi
    
    # Check Python environment
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        if python -c "import streamlit, plotly, pandas" 2>/dev/null; then
            print_success "Python environment validation passed!"
        else
            print_error "Python environment validation failed!"
            return 1
        fi
    else
        print_error "Virtual environment not found!"
        return 1
    fi
    
    return 0
}

# Main execution
main() {
    echo "Starting Firebolt Core NYC Demo production setup..."
    echo "This will:"
    echo "  1. Check prerequisites"
    echo "  2. Setup Firebolt Core"
    echo "  3. Create Python environment"
    echo "  4. Load 21.5M+ NYC parking violations from S3"
    echo "  5. Create performance indexes"
    echo "  6. Validate installation"
    echo ""
    
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    # Record start time
    start_time=$(date +%s)
    
    # Run setup steps
    check_prerequisites
    setup_firebolt_core
    setup_python_environment
    load_production_data
    create_diagnostics_script
    
    # Validate installation
    if validate_installation; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        
        print_success "🎉 Production setup completed successfully!"
        print_success "Setup time: ${duration} seconds"
        echo ""
        echo "🚀 Next steps:"
        echo "  1. Open a new terminal"
        echo "  2. Navigate to this directory: cd $(pwd)"
        echo "  3. Activate environment: source .venv/bin/activate"
        echo "  4. Start Streamlit: streamlit run app/streamlit_app.py"
        echo "  5. Open browser: http://localhost:8501"
        echo ""
        echo "📊 Your system now has 21.5M+ NYC parking violations loaded!"
        echo "🔧 Run './diagnostics.sh' anytime to check system status"
    else
        print_error "Installation validation failed!"
        echo "Run './diagnostics.sh' for detailed system status"
        exit 1
    fi
}

# Run main function
main "$@" 