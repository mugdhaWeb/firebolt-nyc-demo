#!/usr/bin/env python3
"""
Test script to verify filter functionality in the Streamlit app.
This tests the street filter loading issue specifically.
"""

import sys
import subprocess
import time
import logging
from pathlib import Path

# Add the app directory to the path so we can import the connector
sys.path.insert(0, str(Path(__file__).parent / "app"))

from streamlit_app import FireboltConnector, get_filter_data

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_firebolt_connection():
    """Test if Firebolt Core is running and accessible."""
    print("🔍 Testing Firebolt Core connection...")
    
    try:
        result = subprocess.run(
            ["docker", "exec", "firebolt-core", "fb", "-C", "-c", "SELECT 1"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Firebolt Core is running and accessible")
            return True
        else:
            print("❌ Firebolt Core connection failed")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Firebolt Core connection timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

def test_data_exists():
    """Test if the violations table exists and has data."""
    print("🔍 Testing if violations table exists...")
    
    try:
        result = subprocess.run(
            ["docker", "exec", "firebolt-core", "fb", "-C", "-c", "SELECT COUNT(*) FROM violations"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Violations table exists and has data")
            print(f"Output: {result.stdout}")
            return True
        else:
            print("❌ Violations table not found or query failed")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing table: {e}")
        return False

def test_filter_queries():
    """Test individual filter queries directly."""
    print("🔍 Testing filter queries directly...")
    
    queries = {
        "streets": "SELECT DISTINCT street_name FROM violations WHERE street_name IS NOT NULL AND street_name != '' ORDER BY street_name LIMIT 10",
        "amounts": "SELECT DISTINCT calculated_fine_amount FROM violations WHERE calculated_fine_amount IS NOT NULL AND calculated_fine_amount > 0 ORDER BY calculated_fine_amount LIMIT 10",
        "cars": "SELECT DISTINCT vehicle_make FROM violations WHERE vehicle_make IS NOT NULL AND LENGTH(vehicle_make) >= 2 AND vehicle_make != '' ORDER BY vehicle_make LIMIT 10"
    }
    
    for name, query in queries.items():
        print(f"  Testing {name} query...")
        try:
            result = subprocess.run(
                ["docker", "exec", "firebolt-core", "fb", "-C", "-c", query],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                data_lines = [line for line in lines if line and not line.startswith('Time:') and not line.startswith('Request Id:')]
                print(f"    ✅ {name} query successful - got {len(data_lines)} results")
                if data_lines:
                    print(f"    Sample results: {data_lines[:3]}")
            else:
                print(f"    ❌ {name} query failed: {result.stderr}")
                
        except Exception as e:
            print(f"    ❌ Error testing {name}: {e}")

def test_connector_filter_data():
    """Test the get_filter_data function with the FireboltConnector."""
    print("🔍 Testing FireboltConnector and get_filter_data function...")
    
    try:
        # Create connector
        connector = FireboltConnector()
        
        # Test connection
        if not connector.test_connection():
            print("❌ Connector failed to connect")
            return False
            
        print("✅ Connector connected successfully")
        
        # Test get_filter_data
        print("  Testing get_filter_data function...")
        filter_data = get_filter_data(connector)
        
        print(f"  📊 Filter data results:")
        print(f"    Streets: {len(filter_data.get('streets', []))} items")
        print(f"    Amounts: {len(filter_data.get('amounts', []))} items")
        print(f"    Cars: {len(filter_data.get('cars', []))} items")
        
        if filter_data.get('streets'):
            print(f"    Sample streets: {filter_data['streets'][:5]}")
        else:
            print("    ⚠️  No streets loaded!")
            
        if filter_data.get('cars'):
            print(f"    Sample cars: {filter_data['cars'][:5]}")
        else:
            print("    ⚠️  No cars loaded!")
            
        # Test cache behavior
        print("  Testing cache behavior...")
        start_time = time.time()
        filter_data_cached = get_filter_data(connector)
        cache_time = time.time() - start_time
        
        print(f"  Cache hit took {cache_time*1000:.1f}ms")
        
        if len(filter_data_cached.get('streets', [])) == len(filter_data.get('streets', [])):
            print("  ✅ Cache working correctly")
        else:
            print("  ⚠️  Cache inconsistency detected")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing connector: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running comprehensive filter tests...")
    print("=" * 50)
    
    # Test 1: Connection
    if not test_firebolt_connection():
        print("❌ Cannot continue - Firebolt Core not accessible")
        return
    
    # Test 2: Data exists
    if not test_data_exists():
        print("❌ Cannot continue - violations table not found")
        return
    
    # Test 3: Direct queries
    test_filter_queries()
    
    # Test 4: Connector and cache
    test_connector_filter_data()
    
    print("=" * 50)
    print("🎉 Filter testing complete!")

if __name__ == "__main__":
    main() 