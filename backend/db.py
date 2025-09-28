import duckdb

def get_connection():
    conn = duckdb.connect(database=':memory:')
    return conn