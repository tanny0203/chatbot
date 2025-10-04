import pandas as pd
import numpy as np
import warnings
from uuid import UUID
from sqlalchemy.orm import Session
from models.file import File
from models.column_metadata import ColumnMetadata
# Import all models to ensure SQLAlchemy can resolve foreign keys
from models.user import User
from models.chat import Chat
from database.file_storage import FileStorageDB
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import dask.dataframe as dd
import psutil
from functools import lru_cache
import joblib
from pathlib import Path
import re
import scipy

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')
warnings.filterwarnings('ignore', message='.*infer_datetime_format.*')
warnings.filterwarnings('ignore', message='.*Could not infer format.*')
warnings.filterwarnings('ignore', message='.*Parsing dates in.*')

# Map pandas dtypes to SQL types
SQL_TYPE_MAPPING = {
    'int64': 'INTEGER',
    'float64': 'DOUBLE PRECISION',
    'bool': 'BOOLEAN',
    'datetime64[ns]': 'TIMESTAMP',
    'object': 'TEXT',
    'category': 'TEXT'
}

@dataclass
class ValueCount:
    value: str
    count: int

@dataclass
class ColumnAnalysis:
    name: str
    data_type: str
    sql_type: str
    nullable: bool
    is_category: bool
    is_boolean: bool
    is_date: bool
    unique_count: int
    null_count: int
    sample_values: List[str]
    top_values: List[ValueCount]
    enum_values: List[str]
    min: Optional[float]
    max: Optional[float]
    mean: Optional[float]
    median: Optional[float]
    std: Optional[float]
    description: str
    value_mappings: Dict[str, str]
    synonym_mappings: Dict[str, str]
    example_queries: List[str]

class FileService:
    def __init__(self, db: Session, file_storage_url: str = None):
        self.db = db  # Main database session for metadata (File, ColumnMetadata models)
        
        # Import here to avoid circular imports
        from models.database import FILE_STORAGE_DATABASE_URL
        if file_storage_url is None:
            file_storage_url = FILE_STORAGE_DATABASE_URL
        
        # File storage database for actual CSV/Excel data tables    
        self.file_storage = FileStorageDB(file_storage_url)

        # Initialize cache in project folder (Windows-safe)
        base_dir = Path(__file__).resolve().parent
        cache_dir = base_dir / "tmp_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = joblib.Memory(location=str(cache_dir))
        
        # Configure thread pool
        self.executor = ThreadPoolExecutor(
            max_workers=min(32, (os.cpu_count() or 1) * 4)
        )
        
    def _optimize_batch_size(self, df: pd.DataFrame) -> int:
        """Dynamically determine optimal batch size based on data and available memory
        Time Complexity: O(1)
        """
        row_size = df.memory_usage(deep=True).sum() / len(df)
        available_memory = psutil.virtual_memory().available
        return min(
            max(1000, int(available_memory * 0.1 / row_size)),
            50000  # Cap at 50k rows
        )
        
    @lru_cache(maxsize=1000)
    def _detect_special_types(self, sample_data: tuple) -> str:
        """Detect special data types using cached results
        Time Complexity: O(k) where k is sample size (constant)
        """
        sample = pd.Series(sample_data)
        
        patterns = {
            'EMAIL': r'^[\w\.-]+@[\w\.-]+\.\w+$',
            'PHONE': r'^\+?[\d\-\(\)\s]+$',
            'URL': r'^https?://',
            'JSON': r'^[\{\[].*[\}\]]$',
            'DATE': r'^\d{4}-\d{2}-\d{2}',
            'CURRENCY': r'^[\$£€¥]\d+',
            'GEOLOCATION': r'^-?\d+\.\d+,\s*-?\d+\.\d+$'
        }
        
        for type_name, pattern in patterns.items():
            if sample.str.match(pattern).mean() > 0.8:
                return type_name
        return None
        
    async def _smart_load_file(self, file_path: str, filename: str) -> pd.DataFrame:
        """Smart file loading with parallel processing for large files
        Time Complexity: O(n/p) where n is number of rows and p is number of parallel processes
        """
        file_size = os.path.getsize(file_path)
        
        # Determine file type and encoding
        file_extension = filename.lower().split('.')[-1]
        
        if file_extension in ['xlsx', 'xls']:
            # Handle Excel files
            df = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                pd.read_excel,
                file_path
            )
        else:
            # Handle CSV files with encoding detection
            def load_csv_with_encoding(file_path):
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
                
                for encoding in encodings:
                    try:
                        return pd.read_csv(file_path, encoding=encoding)
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                
                # If all encodings fail, try with error handling
                try:
                    return pd.read_csv(file_path, encoding='utf-8', errors='ignore')
                except Exception as e:
                    raise ValueError(f"Could not read CSV file with any encoding: {str(e)}")
            
            if file_size > 500_000_000:  # 500MB
                # Use Dask for large files
                try:
                    ddf = dd.read_csv(file_path, encoding='utf-8')
                    df = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        lambda: ddf.compute()
                    )
                except Exception:
                    # Fallback to pandas with encoding detection
                    df = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        load_csv_with_encoding,
                        file_path
                    )
            else:
                # For smaller files, use pandas with encoding detection
                df = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    load_csv_with_encoding,
                    file_path
                )
            
        return df

    async def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame with parallel type optimization
        Time Complexity: O(n*m/p) where n is rows, m is columns, p is parallel processes
        """
        async def optimize_column(column_name: str) -> Tuple[str, pd.Series]:
            series = df[column_name]
            
            # Run type conversion in thread pool
            loop = asyncio.get_event_loop()
            converted = await loop.run_in_executor(self.executor, self._optimize_column, series)
            return column_name, converted
            
        # Process all columns in parallel
        tasks = [optimize_column(col) for col in df.columns]
        results = await asyncio.gather(*tasks)
        
        # Update DataFrame with optimized columns
        for col_name, converted_series in results:
            df[col_name] = converted_series
                    
        return df
        
    async def _validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Parallel data quality validation
        Time Complexity: O(n*m/p) where n is rows, m is columns, p is parallel processes
        """
        async def analyze_column_quality(column_name: str) -> Tuple[str, Dict[str, Any]]:
            series = df[column_name]
            loop = asyncio.get_event_loop()
            
            # Run analysis in thread pool
            stats = await loop.run_in_executor(self.executor, self._analyze_column_quality, series)
            return column_name, stats
            
        # Analyze all columns in parallel
        tasks = [analyze_column_quality(col) for col in df.columns]
        results = await asyncio.gather(*tasks)
        
        quality_report = {
            'column_stats': dict(results),
            'row_count': len(df),
            'total_size_bytes': df.memory_usage(deep=True).sum()
        }
        
        # Calculate correlations for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 1:
            quality_report['correlations'] = df[numeric_cols].corr().to_dict()
            
        return quality_report

    def _analyze_column_quality(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze quality metrics for a single column
        Time Complexity: O(n) where n is number of rows
        """
        stats = {
            'missing_count': series.isna().sum(),
            'missing_pct': (series.isna().sum() / len(series)) * 100,
            'unique_count': series.nunique(),
            'unique_pct': (series.nunique() / len(series)) * 100
        }
        
        if pd.api.types.is_numeric_dtype(series):
            # Calculate numeric statistics
            clean_series = series.dropna()
            if len(clean_series) > 0:
                stats.update({
                    'min': float(clean_series.min()),
                    'max': float(clean_series.max()),
                    'mean': float(clean_series.mean()),
                    'median': float(clean_series.median()),
                    'std': float(clean_series.std()),
                    # Detect outliers using z-score
                    'outliers': len(np.where(np.abs(scipy.stats.zscore(clean_series)) > 3)[0])
                })
                
        # Detect patterns and special types
        if series.dtype == 'object':
            sample_data = tuple(series.dropna().head(1000))
            stats['special_type'] = self._detect_special_types(sample_data)
            
        return stats
        
    async def _optimize_numeric_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize numeric types with parallel processing
        Time Complexity: O(n*m/p) where n is rows, m is columns, p is parallel processes
        """
        async def optimize_numeric_column(column_name: str) -> Tuple[str, pd.Series]:
            series = df[column_name]
            if not pd.api.types.is_numeric_dtype(series):
                return column_name, series
                
            # Run optimization in thread pool
            loop = asyncio.get_event_loop()
            optimized = await loop.run_in_executor(self.executor, self._optimize_single_numeric_column, series)
            return column_name, optimized
            
        # Optimize all numeric columns in parallel
        tasks = [optimize_numeric_column(col) for col in df.columns]
        results = await asyncio.gather(*tasks)
        
        # Update DataFrame with optimized columns
        for col_name, optimized_series in results:
            df[col_name] = optimized_series
            

        return df

    def _is_date(self, series: pd.Series) -> bool:
        """Check if a series can be parsed as dates"""
        try:
            pd.to_datetime(series)
            return True
        except:
            return False

    def _is_boolean(self, series: pd.Series) -> bool:
        """Check if a series contains boolean-like values"""
        unique_values = set(series.dropna().astype(str).str.lower())
        boolean_sets = [{'true', 'false'}, {'0', '1'}, {'yes', 'no'}, {'y', 'n'}]
        return any(unique_values.issubset(bool_set) for bool_set in boolean_sets)

    def _is_categorical(self, series: pd.Series, threshold: float = 0.05) -> bool:
        """Determine if a column should be treated as categorical"""
        unique_count = series.nunique()
        total_count = len(series)
        
        # Consider as categorical if:
        # 1. Less than threshold% unique values (default 5%)
        # 2. Less than 50 unique values
        return (unique_count / total_count < threshold) or (unique_count < 50)

    def _get_numeric_stats(self, series: pd.Series) -> Dict[str, Optional[float]]:
        """Calculate numeric statistics for a series"""
        if not pd.api.types.is_numeric_dtype(series):
            return {
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'std': None
            }
        
        return {
            'min': float(series.min()) if not pd.isna(series.min()) else None,
            'max': float(series.max()) if not pd.isna(series.max()) else None,
            'mean': float(series.mean()) if not pd.isna(series.mean()) else None,
            'median': float(series.median()) if not pd.isna(series.median()) else None,
            'std': float(series.std()) if not pd.isna(series.std()) else None
        }

    def _optimize_single_numeric_column(self, series: pd.Series) -> pd.Series:
        """Optimize a single numeric column's type"""
        if not pd.api.types.is_numeric_dtype(series):
            return series
            
        # Drop NA values for min/max calculation
        clean_series = series.dropna()
        if len(clean_series) == 0:
            return series
            
        min_val = clean_series.min()
        max_val = clean_series.max()
        
        # Choose the smallest possible int type
        if pd.api.types.is_integer_dtype(series):
            if min_val >= 0:
                if max_val <= 255:
                    return series.astype('uint8')
                elif max_val <= 65535:
                    return series.astype('uint16')
                elif max_val <= 4294967295:
                    return series.astype('uint32')
            else:
                if min_val >= -128 and max_val <= 127:
                    return series.astype('int8')
                elif min_val >= -32768 and max_val <= 32767:
                    return series.astype('int16')
                elif min_val >= -2147483648 and max_val <= 2147483647:
                    return series.astype('int32')
        
        return series

    def _optimize_column(self, series: pd.Series) -> pd.Series:
        """Optimize a single column's type"""
        # Convert to datetime if possible
        if series.dtype == 'object':
            try:
                # Try to convert to datetime with error handling
                # Remove deprecated infer_datetime_format parameter
                # Use errors='coerce' to handle inconsistent formats gracefully
                datetime_result = pd.to_datetime(series, errors='coerce')
                
                # Only return if we successfully converted a reasonable number of values
                # (more than 50% non-null after conversion indicates it's likely a datetime column)
                non_null_before = series.notna().sum()
                non_null_after = datetime_result.notna().sum()
                
                if non_null_after > 0 and (non_null_after / non_null_before) > 0.5:
                    return datetime_result
            except (ValueError, TypeError):
                pass
            
        # Convert to numeric if possible
        if series.dtype == 'object':
            try:
                return pd.to_numeric(series)
            except (ValueError, TypeError):
                pass
                
        # Convert to boolean if possible
        if series.dtype == 'object':
            unique_values = set(series.dropna().astype(str).str.lower())
            if unique_values.issubset({'true', 'false', '1', '0', 'yes', 'no', 'y', 'n'}):
                return series.map({
                    'true': True, 'false': False,
                    '1': True, '0': False,
                    'yes': True, 'no': False,
                    'y': True, 'n': False
                })
                
        # Convert to category if appropriate
        if series.dtype == 'object':
            if series.nunique() / len(series) < 0.05:  # Less than 5% unique values
                return series.astype('category')
                
        return series

    def _analyze_column(self, name: str, series: pd.Series) -> ColumnAnalysis:
        """Analyze a single column and return its metadata"""
        # Basic properties
        is_date = self._is_date(series)
        is_boolean = self._is_boolean(series)
        is_categorical = self._is_categorical(series)
        null_count = series.isna().sum()
        unique_count = series.nunique()

        # Determine data type and SQL type
        if is_date:
            data_type = "DATE"
            sql_type = "DATE"
        elif is_boolean:
            data_type = "BOOLEAN"
            sql_type = "BOOLEAN"
        elif pd.api.types.is_integer_dtype(series):
            data_type = "INTEGER"
            sql_type = "INTEGER"
        elif pd.api.types.is_float_dtype(series):
            data_type = "FLOAT"
            sql_type = "DOUBLE"
        else:
            data_type = "TEXT"
            sql_type = "VARCHAR"

        # Get sample and top values
        sample_values = series.dropna().sample(min(5, len(series))).astype(str).tolist()
        value_counts = series.value_counts().head(10)
        top_values = [
            ValueCount(str(value), int(count))
            for value, count in value_counts.items()
        ]

        # Get enum values for categorical data
        enum_values = []
        if is_categorical:
            enum_values = sorted(series.dropna().unique().astype(str).tolist())

        # Get numeric stats
        numeric_stats = self._get_numeric_stats(series)

        # Generate basic description
        stats_desc = []
        if null_count > 0:
            stats_desc.append(f"Contains {null_count} null values")
        if is_categorical:
            stats_desc.append(f"Has {unique_count} unique values")
        if numeric_stats['min'] is not None:
            stats_desc.append(f"Range: {numeric_stats['min']} to {numeric_stats['max']}")
        
        description = f"{name}: {data_type} column. " + " ".join(stats_desc)
        
        return ColumnAnalysis(
            name=name,
            data_type=data_type,
            sql_type=sql_type,
            nullable=null_count > 0,
            is_category=is_categorical,
            is_boolean=is_boolean,
            is_date=is_date,
            unique_count=unique_count,
            null_count=null_count,
            sample_values=sample_values,
            top_values=top_values,
            enum_values=enum_values,
            min=numeric_stats['min'],
            max=numeric_stats['max'],
            mean=numeric_stats['mean'],
            median=numeric_stats['median'],
            std=numeric_stats['std'],
            description=description,
            value_mappings={},  # Empty for now, can be filled later
            synonym_mappings={},  # Empty for now, can be filled later
            example_queries=[]  # Empty for now, can be filled later
        )

    async def process_file_with_progress(self, file_path: str, filename: str, chat_id: UUID, user_id: UUID, progress_callback) -> Tuple[File, dict]:
        """Process uploaded file and save metadata with progress updates
        Overall Time Complexity:
        - Best Case: O(n*m/p) where n=rows, m=columns, p=parallel processes
        - Worst Case: O(n*m) for large files that can't be fully parallelized
        
        Space Complexity:
        - O(n*m) for main data
        - O(m) for metadata
        """
        try:
            # 1. Smart Load File - O(n/p)
            await progress_callback("loading", 50, "Loading and parsing file data...")
            df = await self._smart_load_file(file_path, filename)
            
            # 2. Clean and prepare column names - O(m)
            await progress_callback("preparing", 60, "Cleaning and preparing data columns...")
            df.columns = df.columns.str.replace('[^0-9a-zA-Z_]', '_', regex=True)
            df.columns = df.columns.str.lower()
            
            # 3. Parallel Processing - All O(n*m/p)
            await progress_callback("analyzing", 70, "Analyzing data types and quality...")
            # Run these tasks in parallel
            tasks = [
                self._prepare_dataframe(df.copy()),  # Type optimization
                self._optimize_numeric_types(df.copy()),  # Numeric optimization
                self._validate_data_quality(df.copy())  # Data quality analysis
            ]
            prepared_df, optimized_df, quality_report = await asyncio.gather(*tasks)
            
            # 4. Generate table name - O(1)
            await progress_callback("metadata", 80, "Generating metadata and table structure...")
            base_name = filename.split('.')[0].lower()
            base_name = ''.join(c if c.isalnum() else '_' for c in base_name)
            table_name = f"{chat_id.hex}_{base_name}"
            
            # 5. Create file record - O(1)
            file_record = File(
                chat_id=chat_id,
                user_id=user_id,
                filename=filename,
                table_name=table_name
            )
            
            # 6. Save to database with optimized batch size - O(n*m/b) where b is batch size
            await progress_callback("storing", 90, "Storing data and metadata to database...")
            batch_size = self._optimize_batch_size(optimized_df)
            
            # 7. Store data in parallel
            async def store_data():
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.file_storage.create_table_for_file,
                    optimized_df,
                    table_name
                )
            
            async def store_metadata():
                # Ensure we're using the correct database session
                # Import here to ensure we get the right engine binding
                from models.database import Base, main_engine
                
                # Make sure all tables exist in the main database
                Base.metadata.create_all(bind=main_engine)
                
                # Save file record
                self.db.add(file_record)
                self.db.commit()
                self.db.refresh(file_record)
                
                # Create column metadata records
                column_metadata = []
                for col_name, stats in quality_report['column_stats'].items():
                    # Convert numpy types to Python native types for database storage
                    def convert_numpy_types(value):
                        if value is None:
                            return None
                        if hasattr(value, 'item'):  # numpy scalar
                            return value.item()
                        if isinstance(value, (np.integer, np.floating)):
                            return value.item()
                        return value
                    
                    metadata = ColumnMetadata(
                        file_id=file_record.id,
                        column_name=col_name,
                        data_type=optimized_df[col_name].dtype.name,
                        sql_type=SQL_TYPE_MAPPING.get(optimized_df[col_name].dtype.name, 'TEXT'),
                        nullable=stats['missing_count'] > 0,
                        is_category=stats['unique_pct'] < 5.0,  # Less than 5% unique values
                        is_boolean=optimized_df[col_name].dtype == 'bool',
                        is_date=pd.api.types.is_datetime64_any_dtype(optimized_df[col_name]),
                        unique_count=convert_numpy_types(stats['unique_count']),
                        null_count=convert_numpy_types(stats['missing_count']),
                        min_value=convert_numpy_types(stats.get('min')),
                        max_value=convert_numpy_types(stats.get('max')),
                        mean_value=convert_numpy_types(stats.get('mean')),
                        median_value=convert_numpy_types(stats.get('median')),
                        std_value=convert_numpy_types(stats.get('std')),
                        sample_values=[str(x) for x in optimized_df[col_name].dropna().head(5).tolist()],
                        top_values=[{'value': str(v), 'count': convert_numpy_types(c)} 
                                  for v, c in optimized_df[col_name].value_counts().head(10).items()],
                        enum_values=[str(x) for x in optimized_df[col_name].unique().tolist()] if stats['unique_pct'] < 5.0 else None,
                        description=f"Column {col_name} with {convert_numpy_types(stats['unique_count'])} unique values"
                    )
                    column_metadata.append(metadata)
                
                self.db.add_all(column_metadata)
                self.db.commit()
            
            # 8. Run database operations in parallel
            await asyncio.gather(store_data(), store_metadata())
            
            await progress_callback("finalizing", 95, "Finalizing processing and generating stats...")
            
            # 9. Prepare response - convert all numpy types to JSON-serializable types
            def make_json_serializable(obj):
                """Recursively convert numpy types and other non-serializable objects to JSON-compatible types"""
                if obj is None:
                    return None
                elif hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                elif isinstance(obj, (np.integer, np.floating, np.bool_)):
                    return obj.item()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {key: make_json_serializable(value) for key, value in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_json_serializable(item) for item in obj]
                elif hasattr(obj, '__dict__'):
                    # Handle objects with attributes by converting to dict
                    return {key: make_json_serializable(value) for key, value in obj.__dict__.items()}
                else:
                    return obj
            
            stats = {
                'row_count': int(len(optimized_df)),
                'column_count': int(len(optimized_df.columns)),
                'quality_report': make_json_serializable(quality_report),
                'table_name': table_name,
                'file_size': int(os.path.getsize(file_path)),
                'created_at': datetime.now().isoformat(),
            }
            
            return file_record, stats
            
        except Exception as e:
            # Cleanup if needed
            raise ValueError(f"Error processing file: {str(e)}")

    async def process_file(self, file_path: str, filename: str, chat_id: UUID, user_id: UUID) -> Tuple[File, dict]:
        """Process uploaded file and save metadata (backward compatibility)
        Overall Time Complexity:
        - Best Case: O(n*m/p) where n=rows, m=columns, p=parallel processes
        - Worst Case: O(n*m) for large files that can't be fully parallelized
        
        Space Complexity:
        - O(n*m) for main data
        - O(m) for metadata
        """
        # Default no-op progress callback for backward compatibility
        async def noop_callback(stage: str, progress: int, message: str):
            pass
            
        return await self.process_file_with_progress(file_path, filename, chat_id, user_id, noop_callback)

    async def _process_file_legacy(self, file_path: str, filename: str, chat_id: UUID, user_id: UUID) -> Tuple[File, dict]:
        """Original process file method - kept for reference"""
        try:
            # 1. Smart Load File - O(n/p)
            df = await self._smart_load_file(file_path, filename)
            
            # 2. Clean and prepare column names - O(m)
            df.columns = df.columns.str.replace('[^0-9a-zA-Z_]', '_', regex=True)
            df.columns = df.columns.str.lower()
            
            # 3. Parallel Processing - All O(n*m/p)
            # Run these tasks in parallel
            tasks = [
                self._prepare_dataframe(df.copy()),  # Type optimization
                self._optimize_numeric_types(df.copy()),  # Numeric optimization
                self._validate_data_quality(df.copy())  # Data quality analysis
            ]
            prepared_df, optimized_df, quality_report = await asyncio.gather(*tasks)
            
            # 4. Generate table name - O(1)
            base_name = filename.split('.')[0].lower()
            base_name = ''.join(c if c.isalnum() else '_' for c in base_name)
            table_name = f"{chat_id.hex}_{base_name}"
            
            # 5. Create file record - O(1)
            file_record = File(
                chat_id=chat_id,
                user_id=user_id,
                filename=filename,
                table_name=table_name
            )
            
            # 6. Save to database with optimized batch size - O(n*m/b) where b is batch size
            batch_size = self._optimize_batch_size(optimized_df)
            
            # 7. Store data in parallel
            async def store_data():
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.file_storage.create_table_for_file,
                    optimized_df,
                    table_name
                )
            
            async def store_metadata():
                # Ensure we're using the correct database session
                # Import here to ensure we get the right engine binding
                from models.database import Base, main_engine
                
                # Make sure all tables exist in the main database
                Base.metadata.create_all(bind=main_engine)
                
                # Save file record
                self.db.add(file_record)
                self.db.commit()
                self.db.refresh(file_record)
                
                # Create column metadata records
                column_metadata = []
                for col_name, stats in quality_report['column_stats'].items():
                    # Convert numpy types to Python native types for database storage
                    def convert_numpy_types(value):
                        if value is None:
                            return None
                        if hasattr(value, 'item'):  # numpy scalar
                            return value.item()
                        if isinstance(value, (np.integer, np.floating)):
                            return value.item()
                        return value
                    
                    metadata = ColumnMetadata(
                        file_id=file_record.id,
                        column_name=col_name,
                        data_type=optimized_df[col_name].dtype.name,
                        sql_type=SQL_TYPE_MAPPING.get(optimized_df[col_name].dtype.name, 'TEXT'),
                        nullable=stats['missing_count'] > 0,
                        is_category=stats['unique_pct'] < 5.0,  # Less than 5% unique values
                        is_boolean=optimized_df[col_name].dtype == 'bool',
                        is_date=pd.api.types.is_datetime64_any_dtype(optimized_df[col_name]),
                        unique_count=convert_numpy_types(stats['unique_count']),
                        null_count=convert_numpy_types(stats['missing_count']),
                        min_value=convert_numpy_types(stats.get('min')),
                        max_value=convert_numpy_types(stats.get('max')),
                        mean_value=convert_numpy_types(stats.get('mean')),
                        median_value=convert_numpy_types(stats.get('median')),
                        std_value=convert_numpy_types(stats.get('std')),
                        sample_values=[str(x) for x in optimized_df[col_name].dropna().head(5).tolist()],
                        top_values=[{'value': str(v), 'count': convert_numpy_types(c)} 
                                  for v, c in optimized_df[col_name].value_counts().head(10).items()],
                        enum_values=[str(x) for x in optimized_df[col_name].unique().tolist()] if stats['unique_pct'] < 5.0 else None,
                        description=f"Column {col_name} with {convert_numpy_types(stats['unique_count'])} unique values"
                    )
                    column_metadata.append(metadata)
                
                self.db.add_all(column_metadata)
                self.db.commit()
            
            # 8. Run database operations in parallel
            await asyncio.gather(store_data(), store_metadata())
            
            # 9. Prepare response - convert all numpy types to JSON-serializable types
            def make_json_serializable(obj):
                """Recursively convert numpy types and other non-serializable objects to JSON-compatible types"""
                if obj is None:
                    return None
                elif hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                elif isinstance(obj, (np.integer, np.floating, np.bool_)):
                    return obj.item()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {key: make_json_serializable(value) for key, value in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_json_serializable(item) for item in obj]
                elif hasattr(obj, '__dict__'):
                    # Handle objects with attributes by converting to dict
                    return {key: make_json_serializable(value) for key, value in obj.__dict__.items()}
                else:
                    return obj
            
            stats = {
                'row_count': int(len(optimized_df)),
                'column_count': int(len(optimized_df.columns)),
                'quality_report': make_json_serializable(quality_report),
                'table_name': table_name,
                'file_size': int(os.path.getsize(file_path)),
                'created_at': datetime.now().isoformat(),
            }
            
            return file_record, stats
            
        except Exception as e:
            # Cleanup if needed
            raise ValueError(f"Error processing file: {str(e)}")
        
        # Create file record
        file_record = File(
            chat_id=chat_id,
            user_id=user_id,
            filename=filename,
            table_name=table_name
        )
        
        try:
            # Store the data in the file storage database
            self.file_storage.create_table_for_file(df, table_name)
        except Exception as e:
            raise ValueError(f"Error storing file data: {str(e)}")
        
        # Save file record first to get the ID
        self.db.add(file_record)
        self.db.commit()
        self.db.refresh(file_record)

        # Analyze each column and create metadata records
        columns_metadata = {}
        for column_name in df.columns:
            metadata = self._analyze_column(column_name, df[column_name])
            
            # Create column metadata record
            column_metadata = ColumnMetadata(
                file_id=file_record.id,
                column_name=column_name,
                data_type=metadata.data_type,
                sql_type=metadata.sql_type,
                nullable=metadata.nullable,
                is_category=metadata.is_category,
                is_boolean=metadata.is_boolean,
                is_date=metadata.is_date,
                unique_count=metadata.unique_count,
                null_count=metadata.null_count,
                
                # Numeric statistics
                min_value=metadata.min,
                max_value=metadata.max,
                mean_value=metadata.mean,
                median_value=metadata.median,
                std_value=metadata.std,
                
                # JSONB fields
                sample_values=metadata.sample_values,
                top_values=[{'value': tv.value, 'count': tv.count} for tv in metadata.top_values],
                enum_values=metadata.enum_values,
                value_mappings=metadata.value_mappings or {},
                synonym_mappings=metadata.synonym_mappings or {},
                example_queries=metadata.example_queries or [],
                description=metadata.description
            )
            
            self.db.add(column_metadata)
            
            # Store in response dictionary
            columns_metadata[column_name] = {
                'name': column_name,
                'data_type': metadata.data_type,
                'sql_type': metadata.sql_type,
                'nullable': metadata.nullable,
                'is_category': metadata.is_category,
                'is_boolean': metadata.is_boolean,
                'is_date': metadata.is_date,
                'unique_count': metadata.unique_count,
                'null_count': metadata.null_count,
                'sample_values': metadata.sample_values,
                'top_values': [{'value': tv.value, 'count': tv.count} for tv in metadata.top_values],
                'enum_values': metadata.enum_values,
                'min': metadata.min,
                'max': metadata.max,
                'mean': metadata.mean,
                'median': metadata.median,
                'std': metadata.std,
                'description': metadata.description,
                'value_mappings': metadata.value_mappings,
                'synonym_mappings': metadata.synonym_mappings,
                'example_queries': metadata.example_queries
            }

        # Save all column metadata
        self.db.commit()

        # Comprehensive statistics and analysis for response
        stats = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': columns_metadata,
            'sample_rows': df.head().to_dict(),
            'table_name': table_name,
            'file_size': os.path.getsize(file_path),
            'created_at': datetime.now().isoformat(),
        }

        return file_record, stats

    def get_file_metadata(self, file_id: UUID) -> Dict[str, Any]:
        """Retrieve metadata for a specific file"""
        # Get file record and its columns
        file_record = self.db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise ValueError(f"File with id {file_id} not found")

        # Get all column metadata for the file
        columns = (self.db.query(ColumnMetadata)
                  .filter(ColumnMetadata.file_id == file_id)
                  .all())

        # Organize metadata
        columns_metadata = {}
        for col in columns:
            columns_metadata[col.column_name] = {
                'name': col.column_name,
                'data_type': col.data_type,
                'sql_type': col.sql_type,
                'nullable': col.nullable,
                'is_category': col.is_category,
                'is_boolean': col.is_boolean,
                'is_date': col.is_date,
                'unique_count': col.unique_count,
                'null_count': col.null_count,
                'sample_values': col.sample_values,
                'top_values': col.top_values,
                'enum_values': col.enum_values,
                'min': col.min_value,
                'max': col.max_value,
                'mean': col.mean_value,
                'median': col.median_value,
                'std': col.std_value,
                'description': col.description,
                'value_mappings': col.value_mappings,
                'synonym_mappings': col.synonym_mappings,
                'example_queries': col.example_queries
            }

        return {
            'file_id': file_record.id,
            'filename': file_record.filename,
            'table_name': file_record.table_name,
            'columns': columns_metadata
        }