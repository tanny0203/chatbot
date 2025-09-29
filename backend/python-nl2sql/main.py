from fastapi import FastAPI, UploadFile, File
import pandas as pd
from db import get_connection
import io
from pydantic import BaseModel
import numpy as np

app = FastAPI()

conn = get_connection()

class QueryRequest(BaseModel):
    sql: str

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()

    if file.filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
    elif file.filename.endswith('.xlsx'):
        df = pd.read_excel(io.BytesIO(content))
    else:
        return {"error": "Unsupported file type"}

    table_name = file.filename.split(".")[0]

    conn.execute(f"CREATE OR REPLACE TABLE \"{table_name}\" AS SELECT * FROM df")

    metadata = f"Table {table_name}\n"
    metadata += f"Columns:\n"
    for col, dtype in df.dtypes.items():
        metadata += f" - {col}: {dtype}\n"
    metadata += f"Row count: {len(df)}\n"


    sample_rows = df.head().where(pd.notnull(df.head()), None).to_dict(orient="records")
    return {
        "message": f"Uploaded {file.filename} successfully",
        "table": table_name,
        "metadata": metadata,
        "sample_rows": sample_rows
    }


@app.post("/query")
async def run_query(request: QueryRequest):
    sql = request.sql
    try:
        df = conn.execute(sql).df()
        df = df.replace([np.inf, -np.inf, np.nan], None)
        result = df.to_dict(orient="records")
        return {"query": sql, "result": result}
    except Exception as e:
        return {"error": str(e)}