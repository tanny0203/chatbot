def test_column_metadata_comprehensive(df, metadata_list, verbose=False):
    """
    Comprehensive test function to verify metadata accuracy for any dataset.
    
    Args:
        df: pandas DataFrame
        metadata_list: List of metadata dictionaries
        verbose: If True, shows detailed test results
        
    Returns:
        dict: Test results with total_columns, passed_columns, success_rate, failed_tests, status
    """
    import pandas as pd
    import numpy as np
    
    if verbose:
        print("=" * 60)
        print("COLUMN METADATA COMPREHENSIVE TEST")
        print("=" * 60)
    
    total_columns = len(df.columns)
    metadata_columns = len(metadata_list)
    passed_tests = 0
    failed_tests = []
    
    if verbose:
        print(f"Dataset: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"Metadata entries: {metadata_columns}")
        print()
    
    # Test 1: Column count match
    if total_columns != metadata_columns:
        failed_tests.append(f"CRITICAL: Column count mismatch - dataset={total_columns}, metadata={metadata_columns}")
        return {
            "total_columns": total_columns,
            "passed_columns": 0,
            "success_rate": 0.0,
            "failed_tests": failed_tests,
            "status": "FAILED"
        }
    
    # Create metadata lookup
    metadata_dict = {item['column_name']: item for item in metadata_list}
    
    # Check for missing columns in metadata
    missing_columns = [col for col in df.columns if col not in metadata_dict]
    if missing_columns:
        failed_tests.extend([f"CRITICAL: Column '{col}' missing from metadata" for col in missing_columns])
    
    for col in df.columns:
        if col not in metadata_dict:
            continue
            
        col_data = df[col]
        meta = metadata_dict[col]
        col_failed = False
        
        # Core tests that must pass
        actual_unique = col_data.nunique(dropna=True)
        actual_nulls = col_data.isnull().sum()
        
        # Test basic counts
        if meta['unique_count'] != actual_unique:
            failed_tests.append(f"{col}: unique_count {meta['unique_count']} ≠ actual {actual_unique}")
            col_failed = True
            
        if meta['null_count'] != actual_nulls:
            failed_tests.append(f"{col}: null_count {meta['null_count']} ≠ actual {actual_nulls}")
            col_failed = True
        
        # Test data type classification
        is_integer = pd.api.types.is_integer_dtype(col_data.dtype)
        is_float = pd.api.types.is_float_dtype(col_data.dtype)
        is_bool = pd.api.types.is_bool_dtype(col_data.dtype)
        is_datetime = pd.api.types.is_datetime64_any_dtype(col_data.dtype)
        
        expected_data_type = (
            'INTEGER' if is_integer else
            'FLOAT' if is_float else
            'BOOLEAN' if is_bool else
            'DATE' if is_datetime else
            'TEXT'
        )
        
        if meta['data_type'] != expected_data_type:
            failed_tests.append(f"{col}: data_type '{meta['data_type']}' ≠ expected '{expected_data_type}'")
            col_failed = True
            
        # Test boolean flags
        expected_nullable = col_data.isnull().any()
        if meta['nullable'] != expected_nullable:
            failed_tests.append(f"{col}: nullable {meta['nullable']} ≠ expected {expected_nullable}")
            col_failed = True
            
        expected_is_category = (actual_unique <= 20 and expected_data_type not in ['BOOLEAN', 'DATE'])
        if meta['is_category'] != expected_is_category:
            failed_tests.append(f"{col}: is_category {meta['is_category']} ≠ expected {expected_is_category}")
            col_failed = True
        
        # Test numeric statistics for numeric columns
        if expected_data_type in ['INTEGER', 'FLOAT'] and not col_data.dropna().empty:
            clean_data = col_data.dropna()
            
            expected_min = float(clean_data.min())
            if meta['min_value'] is None or abs(meta['min_value'] - expected_min) > 1e-10:
                failed_tests.append(f"{col}: min_value {meta['min_value']} ≠ expected {expected_min}")
                col_failed = True
                
            expected_max = float(clean_data.max())
            if meta['max_value'] is None or abs(meta['max_value'] - expected_max) > 1e-10:
                failed_tests.append(f"{col}: max_value {meta['max_value']} ≠ expected {expected_max}")
                col_failed = True
                
            expected_mean = float(clean_data.mean())
            if meta['mean_value'] is None or abs(meta['mean_value'] - expected_mean) > 1e-10:
                failed_tests.append(f"{col}: mean_value {meta['mean_value']} ≠ expected {expected_mean}")
                col_failed = True
        else:
            # Non-numeric columns should have None for numeric stats
            numeric_fields = ['min_value', 'max_value', 'mean_value', 'median_value', 'std_value']
            for field in numeric_fields:
                if meta[field] is not None:
                    failed_tests.append(f"{col}: {field} should be None for non-numeric column, got {meta[field]}")
                    col_failed = True
        
        # Test JSONB fields structure
        if not isinstance(meta['sample_values'], list):
            failed_tests.append(f"{col}: sample_values must be a list")
            col_failed = True
        elif len(meta['sample_values']) > 5:
            failed_tests.append(f"{col}: sample_values cannot have more than 5 items")
            col_failed = True
            
        if not isinstance(meta['top_values'], list):
            failed_tests.append(f"{col}: top_values must be a list")
            col_failed = True
        elif meta['top_values']:
            # Verify structure of top_values
            for i, item in enumerate(meta['top_values']):
                if not isinstance(item, dict) or 'value' not in item or 'count' not in item:
                    failed_tests.append(f"{col}: top_values[{i}] must have 'value' and 'count' keys")
                    col_failed = True
                    break
        
        # Test enum_values for categorical columns
        if meta['is_category']:
            if meta['enum_values'] is None:
                failed_tests.append(f"{col}: enum_values cannot be None for categorical column")
                col_failed = True
            elif not isinstance(meta['enum_values'], list):
                failed_tests.append(f"{col}: enum_values must be a list for categorical column")
                col_failed = True
        
        # Count passed columns
        if not col_failed:
            passed_tests += 1
    
    # Calculate results
    success_rate = (passed_tests / total_columns) * 100 if total_columns > 0 else 0
    status = "PASSED" if len(failed_tests) == 0 else "FAILED"
    
    if verbose:
        print(f"RESULTS:")
        print(f"Columns tested: {total_columns}")
        print(f"Columns passed: {passed_tests}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Status: {status}")
        print()
        
        if failed_tests:
            print("FAILED TESTS:")
            for i, fail in enumerate(failed_tests):
                if i < 20:  # Show first 20 failures
                    print(f"  • {fail}")
            if len(failed_tests) > 20:
                print(f"  ... and {len(failed_tests) - 20} more failures")
        else:
            print("✅ ALL TESTS PASSED!")
        
        print("=" * 60)
    
    return {
        "total_columns": total_columns,
        "passed_columns": passed_tests,
        "success_rate": success_rate,
        "failed_tests": failed_tests,
        "status": status
    }

# Simple wrapper for quick testing
def quick_metadata_test(dataframe, metadata):
    """
    Simple function that returns just the essential test results.
    
    Returns:
        dict: {
            'total_columns': int,
            'passed_columns': int, 
            'success_rate': float,
            'status': 'PASSED'/'FAILED',
            'error_count': int
        }
    """
    result = test_column_metadata_comprehensive(dataframe, metadata, verbose=False)
    return {
        'total_columns': result['total_columns'],
        'passed_columns': result['passed_columns'],
        'success_rate': result['success_rate'],
        'status': result['status'],
        'error_count': len(result['failed_tests'])
    }
