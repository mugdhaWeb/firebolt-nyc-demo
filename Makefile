.PHONY: all setup-core load-data create-indexes install-deps run-app clean help

# Default target
all: setup-core load-data create-indexes install-deps run-app

# Setup Firebolt Core
setup-core:
	@echo "🚀 Setting up Firebolt Core..."
	chmod +x setup_core.sh
	./setup_core.sh

# Prepare dataset
prepare-data:
	@echo "📊 Preparing dataset..."
	python scripts/download_dataset.py

# Load data into Firebolt Core
load-data: prepare-data
	@echo "📥 Loading NYC parking violations data..."
	@echo "⚠️  Note: Data loading requires manual execution due to memory constraints"
	@echo "Run individual SQL commands from sql/02_load_data.sql manually"

# Create performance indexes
create-indexes:
	@echo "🎯 Creating performance indexes..."
	@echo "⚠️  Note: Index creation requires manual execution"
	@echo "Run individual SQL commands from sql/03_create_indexes.sql manually"

# Install Python dependencies
install-deps:
	@echo "📦 Setting up Python environment..."
	python3 -m venv .venv || python -m venv .venv
	@echo "📦 Installing Python dependencies..."
	.venv/bin/pip install -r requirements.txt || .venv/Scripts/pip.exe install -r requirements.txt

# Run the Streamlit app
run-app:
	@echo "🚀 Starting Streamlit app..."
	@echo "Open your browser to: http://localhost:8501"
	@echo "💡 Make sure to activate virtual environment if running manually:"
	@echo "   source .venv/bin/activate  # Linux/Mac"
	@echo "   .venv\\Scripts\\activate     # Windows"
	.venv/bin/streamlit run app/streamlit_app.py || .venv/Scripts/streamlit.exe run app/streamlit_app.py

# Clean up Docker resources
clean:
	@echo "🧹 Cleaning up..."
	docker stop firebolt-core || true
	docker rm firebolt-core || true
	docker volume prune -f
	rm -rf data/

# Reset everything and start fresh
reset: clean all

# Show status of Firebolt Core
status:
	@echo "📊 Firebolt Core Status:"
	@docker ps | grep firebolt-core || echo "❌ Firebolt Core not running"
	@echo ""
	@echo "🔍 Testing connection..."
	@docker exec firebolt-core fb -C -c "SELECT 'Firebolt Core is responsive!' as status" 2>/dev/null || echo "❌ Cannot connect to Firebolt Core"

# Run benchmark queries for testing
test-queries:
	@echo "🏃 Running benchmark queries..."
	@echo "Q1: Fiscal year aggregation"
	@docker exec firebolt-core fb -C -c "SELECT EXTRACT(YEAR FROM issue_date) as year, COUNT(*) as violations FROM violations GROUP BY EXTRACT(YEAR FROM issue_date) ORDER BY year;"
	@echo ""
	@echo "Q2: Top streets by revenue"
	@docker exec firebolt-core fb -C -c "SELECT street_name, SUM(fine_amount) as revenue FROM violations WHERE street_name IS NOT NULL GROUP BY street_name ORDER BY revenue DESC LIMIT 5;"

# Debug connectivity issues
debug:
	@echo "🔍 Firebolt Core Debug Information"
	@echo "=================================="
	@echo ""
	@echo "📋 Docker Status:"
	@docker --version || echo "❌ Docker not found"
	@echo ""
	@echo "📋 Container Status:"
	@docker ps -a | grep firebolt-core || echo "❌ No firebolt-core container found"
	@echo ""
	@echo "📋 Container Logs (last 10 lines):"
	@docker logs firebolt-core --tail 10 2>/dev/null || echo "❌ Cannot access container logs"
	@echo ""
	@echo "📋 Test Connection:"
	@docker exec firebolt-core fb -C -c "SELECT 'Connection successful!' as status" 2>/dev/null || echo "❌ Connection failed"

# Fix common issues
fix:
	@echo "🔧 Attempting to fix common issues..."
	@echo "Stopping existing container..."
	@docker stop firebolt-core 2>/dev/null || true
	@echo "Removing existing container..."
	@docker rm firebolt-core 2>/dev/null || true
	@echo "Restarting Firebolt Core..."
	@make setup-core

# Show help
help:
	@echo "🚗 Firebolt Core NYC Parking Demo"
	@echo ""
	@echo "Available commands:"
	@echo "  make all           - Complete setup and start the app"
	@echo "  make setup-core    - Install and start Firebolt Core"
	@echo "  make load-data     - Load NYC parking violations data"
	@echo "  make create-indexes - Create performance indexes"
	@echo "  make install-deps  - Install Python dependencies (with venv)"
	@echo "  make run-app       - Start the Streamlit app"
	@echo "  make status        - Check Firebolt Core status"
	@echo "  make test-queries  - Run sample benchmark queries"
	@echo "  make debug         - Show detailed debug information"
	@echo "  make fix           - Fix common connectivity issues"
	@echo "  make clean         - Remove all Docker resources"
	@echo "  make reset         - Clean and restart everything"
	@echo "  make help          - Show this help message" 