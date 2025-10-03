from sqlalchemy import create_engine, text
from contextlib import contextmanager
import pandas as pd

class FileStorageDB:
    def __init__(self, db_url="postgresql://balaji:balaji2005@localhost:5432/filestorage?sslmode=disable"):
        self.engine = create_engine(db_url)

    @contextmanager
    def get_connection(self):
        """Get a connection from the connection pool"""
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def create_table_for_file(self, df, table_name: str):
        """Create a table for the DataFrame with optimized types"""
        # Drop table if exists
        with self.get_connection() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
            conn.commit()
            
            # Use pandas to_sql with the most efficient method
            df.to_sql(
                name=table_name,
                con=self.engine,
                if_exists='replace',
                index=False,
                method='multi',  # Uses executemany for better performance
                chunksize=10000  # Process 10000 rows at a time
            )

    def get_table_sample(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Get a sample of rows from a table"""
        query = f'SELECT * FROM "{table_name}" LIMIT {limit}'
        return pd.read_sql(query, self.engine)

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        return pd.read_sql(query, self.engine)