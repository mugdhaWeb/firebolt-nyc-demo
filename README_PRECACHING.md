# Pre-caching Queries

This project implements automatic query pre-caching to ensure optimal performance and guarantee that analytical queries always return real data.

## How It Works

During data ingestion (`./load_data.sh`), the system automatically:

1. **Loads and validates data** from S3 into the violations table
2. **Creates performance indexes** for optimal query execution  
3. **Silently pre-caches** the 5 main analytical queries plus filter data
4. **Validates results** to ensure each query returns > 0 rows
5. **Logs performance metrics** to `precache.log`

## Pre-cached Queries

The following queries are automatically pre-cached:

- **Q1**: Total violations & fines summary (aggregation statistics)
- **Q2**: Revenue by street (top 10 streets by revenue)
- **Q3**: Vehicle make analysis (violations by vehicle make)
- **Q4**: Yearly trend analysis (violations by year)
- **Q5**: Interactive data filtering (sample data with fine categories)

Plus filter data queries:
- All distinct street names
- All distinct fine amounts  
- All distinct vehicle makes
- Sample data for data browser

## Performance Guarantees

- ✅ **No empty results**: Script fails if any query returns 0 rows
- ✅ **Sub-200ms queries**: All pre-cached queries execute in < 200ms
- ✅ **Automatic validation**: Built-in checks ensure data integrity
- ✅ **Silent operation**: Pre-caching happens transparently during setup

## Validation

To verify pre-caching is working correctly:

```bash
# Run the validation test suite
python3 test_precache_validation.py
```

The test validates:
- All 9 queries (5 main + 4 filter) return data
- No "empty results" messages
- Query performance within acceptable limits
- `precache.log` contains success entries

## Files

- `load_data.sh` - Main data loading script with integrated pre-caching
- `precache.log` - Performance and validation log (created during execution)
- `test_precache_validation.py` - Comprehensive test suite
- `ci_run.log` - Full execution log for debugging

## Error Handling

If any pre-cached query fails or returns empty results:
- Script exits with code 99
- Error message indicates which query failed
- Full details logged to `precache.log`
- Data ingestion considered incomplete

This ensures the demo always provides a fast, reliable experience with guaranteed real data results. 