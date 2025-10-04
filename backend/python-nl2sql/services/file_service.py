import re
import pandas as pd
import numpy as np
from uuid import uuid4
import sqlalchemy
from sqlalchemy import create_engine, text
from models.column_metadata import ColumnMetadata
from sqlalchemy.orm import Session



def infer_sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return 'INTEGER'
    elif pd.api.types.is_float_dtype(dtype):
        return 'DOUBLE'
    elif pd.api.types.is_bool_dtype(dtype):
        return 'BOOLEAN'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'DATE'
    else:
        return 'VARCHAR'

def get_column_metadata(df: pd.DataFrame, file_id):
    metadata = []
    for col in df.columns:
        data = df[col]
        col_dtype = data.dtype
        data_type = (
            'INTEGER' if pd.api.types.is_integer_dtype(col_dtype) else
            'FLOAT' if pd.api.types.is_float_dtype(col_dtype) else
            'BOOLEAN' if pd.api.types.is_bool_dtype(col_dtype) else
            'DATE' if pd.api.types.is_datetime64_any_dtype(col_dtype) else
            'TEXT'
        )
        sql_type = infer_sql_type(col_dtype)
        nullable = bool(data.isnull().any())
        unique_count = int(data.nunique(dropna=True))
        null_count = int(data.isnull().sum())
        is_category = str(col_dtype) == "category" or (unique_count <= 20 and data_type != 'BOOLEAN' and data_type != 'DATE')
        is_boolean = data_type == 'BOOLEAN'
        is_date = data_type == 'DATE'

        # Numeric stats
        num_stats = data.dropna() if data_type in ['INTEGER', 'FLOAT'] else None
        min_value = float(num_stats.min()) if num_stats is not None and not num_stats.empty else None
        max_value = float(num_stats.max()) if num_stats is not None and not num_stats.empty else None
        mean_value = float(num_stats.mean()) if num_stats is not None and not num_stats.empty else None
        median_value = float(num_stats.median()) if num_stats is not None and not num_stats.empty else None
        std_value = float(num_stats.std()) if num_stats is not None and not num_stats.empty else None

        # JSONB-like fields - convert numpy types to native Python types
        def convert_numpy_types(value):
            """Convert numpy types to native Python types for JSON serialization"""
            if hasattr(value, 'item'):
                return value.item()
            elif isinstance(value, np.integer):
                return int(value)
            elif isinstance(value, np.floating):
                return float(value)
            elif isinstance(value, np.bool_):
                return bool(value)
            else:
                return value

        sample_values = [convert_numpy_types(item) for item in data.dropna().sample(min(5, len(data.dropna())), random_state=1).tolist()] if not data.dropna().empty else []
        top_values = (
            [{'value': convert_numpy_types(k), 'count': int(v)} for k, v in data.value_counts(dropna=True).head(5).items()]
            if not data.dropna().empty else []
        )
        enum_values = [convert_numpy_types(item) for item in data.unique().tolist()] if is_category else None
        
        # Generate intelligent value mappings for categorical data
        value_mappings = {}
        if is_category and enum_values:
            # Create human-readable mappings for common patterns
            for val in enum_values[:10]:  # Limit to first 10 values
                val_str = str(val).lower()
                if val_str in ['m', 'male', '1'] and data_type != 'INTEGER':
                    value_mappings[str(val)] = "Male"
                elif val_str in ['f', 'female', '0'] and data_type != 'INTEGER':
                    value_mappings[str(val)] = "Female"
                elif val_str in ['y', 'yes', 'true', '1'] and data_type != 'INTEGER':
                    value_mappings[str(val)] = "Yes"
                elif val_str in ['n', 'no', 'false', '0'] and data_type != 'INTEGER':
                    value_mappings[str(val)] = "No"
        
        # Generate synonym mappings for better query understanding
        synonym_mappings = {}
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['age', 'year', 'born']):
            synonym_mappings[col] = ["age", "years old", "birth year", "born in"]
        elif any(keyword in col_lower for keyword in ['name', 'title', 'label']):
            synonym_mappings[col] = ["name", "title", "called", "named"]
        elif any(keyword in col_lower for keyword in ['gender', 'sex']):
            synonym_mappings[col] = ["gender", "sex", "male or female"]
        elif any(keyword in col_lower for keyword in ['score', 'grade', 'mark', 'point']):
            synonym_mappings[col] = ["score", "grade", "marks", "points", "rating"]
        elif any(keyword in col_lower for keyword in ['country', 'nation', 'location']):
            synonym_mappings[col] = ["country", "nation", "location", "from"]
        
        # Generate example queries based on column type and content
        example_queries = []
        if data_type in ['INTEGER', 'FLOAT']:
            if min_value is not None and max_value is not None:
                example_queries = [
                    f"What is the average {col}?",
                    f"Show records where {col} is greater than {min_value + (max_value - min_value) * 0.5:.1f}",
                    f"What is the maximum {col}?"
                ]
        elif is_category and enum_values:
            sample_val = enum_values[0] if enum_values else "value"
            example_queries = [
                f"How many records have {col} = '{sample_val}'?",
                f"Show all unique values for {col}",
                f"Group by {col} and count"
            ]
        elif data_type == 'TEXT':
            example_queries = [
                f"Search for records where {col} contains 'keyword'",
                f"Show distinct {col} values",
                f"Count records by {col}"
            ]
        
        # Generate intelligent description
        description_parts = []
        description_parts.append(f"{data_type.lower()} column")
        
        if is_category:
            description_parts.append(f"with {unique_count} categories")
        elif data_type in ['INTEGER', 'FLOAT']:
            if min_value is not None and max_value is not None:
                description_parts.append(f"ranging from {min_value} to {max_value}")
        
        if null_count > 0:
            null_pct = (null_count / len(data)) * 100
            description_parts.append(f"{null_pct:.1f}% missing values")
        
        description = f"{col}: " + ", ".join(description_parts).capitalize()

        column_metadata = ColumnMetadata(
            id=uuid4(),
            file_id=file_id,
            column_name=col,
            data_type=data_type,
            sql_type=sql_type,
            nullable=nullable,
            is_category=bool(is_category),
            is_boolean=bool(is_boolean),
            is_date=bool(is_date),
            unique_count=int(unique_count),
            null_count=int(null_count),
            min_value=float(min_value) if min_value is not None else None,
            max_value=float(max_value) if max_value is not None else None,
            mean_value=float(mean_value) if mean_value is not None else None,
            median_value=float(median_value) if median_value is not None else None,
            std_value=float(std_value) if std_value is not None else None,
            sample_values=sample_values,
            top_values=top_values,
            enum_values=enum_values,
            value_mappings=value_mappings,
            synonym_mappings=synonym_mappings,
            example_queries=example_queries,
            description=description,
        )
        metadata.append(column_metadata)
    return metadata


def clean_column_name(col_name: str, used_names: set) -> str:
    """Clean and ensure unique column names for PostgreSQL"""
    clean_col = re.sub(r'[^a-zA-Z0-9_]', '_', str(col_name)).lower()
    
    # Handle names starting with digits
    if clean_col and clean_col[0].isdigit():
        clean_col = f"col_{clean_col}"
    
    # Handle empty names
    if not clean_col:
        clean_col = "unnamed_column"
    
    # Handle reserved words
    reserved_words = {'order', 'group', 'table', 'select', 'where', 'from', 'insert', 'update', 'delete', 'user', 'index'}
    if clean_col in reserved_words:
        clean_col = f"{clean_col}_col"
    
    # Ensure uniqueness
    original_clean = clean_col
    counter = 1
    while clean_col in used_names:
        clean_col = f"{original_clean}_{counter}"
        counter += 1
    
    used_names.add(clean_col)
    return clean_col


def clean_table_name(table_name: str) -> str:
    """Clean table name for PostgreSQL compatibility"""
    # Remove file extensions and special characters
    clean_name = re.sub(r'\.(csv|xlsx?|json|txt)$', '', table_name, flags=re.IGNORECASE)
    # Replace all non-alphanumeric characters with underscores
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', clean_name).lower()
    
    # Handle names starting with digits
    if clean_name and clean_name[0].isdigit():
        clean_name = f"table_{clean_name}"
    
    # Handle empty names
    if not clean_name:
        clean_name = f"table_{str(uuid4()).replace('-', '_')}"
    
    # Truncate if too long (PostgreSQL limit is 63 characters)
    if len(clean_name) > 60:  # Leave room for potential suffixes
        clean_name = clean_name[:60]
    
    return clean_name


def create_table_sql(sql: str, table_name: str, conn: sqlalchemy.Engine):
    """Execute the CREATE TABLE SQL statement"""
    with conn.connect() as connection:
        with connection.begin():
            connection.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
            connection.execute(text(sql))

def generate_table_schema(df: pd.DataFrame, table_name=None):
    """
    Generate accurate PostgreSQL CREATE TABLE schema for uploaded CSV/XLSX.
    Optimized for reliability and best SQL performance.
    """
    
    if table_name is None:
        table_name = f"uploaded_data_{str(uuid4())}"
    
    columns = []
    used_names = set()
    
    for col in df.columns:
        # Clean column name for PostgreSQL
        clean_col = clean_column_name(col, used_names)
        
        # Handle SQL reserved keywords
        reserved_words = ['order', 'group', 'table', 'select', 'where', 'from', 'insert', 'update', 'delete', 'user', 'index']
        if clean_col in reserved_words:
            clean_col = f"{clean_col}_col"
        
        data = df[col]
        
        # Determine best SQL type with smart analysis
        if pd.api.types.is_integer_dtype(data.dtype):
            # Check actual range for optimal integer type
            min_val, max_val = data.min(), data.max()
            if -32768 <= min_val and max_val <= 32767:
                sql_type = "SMALLINT"  # Most efficient for small ranges
            elif -2147483648 <= min_val and max_val <= 2147483647:
                sql_type = "INTEGER"
            else:
                sql_type = "BIGINT"
                
        elif pd.api.types.is_float_dtype(data.dtype):
            sql_type = "DOUBLE PRECISION"
                
        elif pd.api.types.is_bool_dtype(data.dtype):
            sql_type = "BOOLEAN"
            
        elif pd.api.types.is_datetime64_any_dtype(data.dtype):
            sql_type = "TIMESTAMP"
            
        else:  # Text/object columns
            if data.dropna().empty:
                varchar_len = 255
            else:
                max_len = data.astype(str).str.len().max()
                # Optimized VARCHAR sizing for performance
                if max_len <= 5:
                    varchar_len = 20    # Very short codes
                elif max_len <= 20:
                    varchar_len = 50    # Short text
                elif max_len <= 100:
                    varchar_len = 200   # Medium text
                elif max_len <= 500:
                    varchar_len = 1000  # Long text
                else:
                    varchar_len = 5000  # Very long text
            
            sql_type = f"VARCHAR({varchar_len})"
        
        # NULL constraint based on actual data
        nullable = "NULL" if data.isnull().any() else "NOT NULL"
        
        columns.append(f'    "{clean_col}" {sql_type} {nullable}')
    
    # Generate final SQL with proper formatting
    sql = f"""CREATE TABLE {table_name} (
            id SERIAL PRIMARY KEY,
            {',\n'.join(columns)},
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );"""
    
    return sql


def save_table_metadata(metadata_list: list[ColumnMetadata], db: Session):
    db.add_all(metadata_list)
    db.commit()

def insert_values(df: pd.DataFrame, table_name: str, conn: sqlalchemy.Engine):
    """Insert DataFrame values safely and efficiently using pandas to_sql"""
    # Clean column names to match the table schema
    df_clean = df.copy()
    used_names = set()
    column_mapping = {}
    
    for col in df.columns:
        clean_col = clean_column_name(col, used_names)
        column_mapping[col] = clean_col
    
    df_clean.rename(columns=column_mapping, inplace=True)
    
    df_clean.to_sql(
        name=table_name,
        con=conn,
        if_exists='replace',
        index=False,
        method='multi',
        chunksize=1000
    )
