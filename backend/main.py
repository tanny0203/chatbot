from fastapi import FastAPI, UploadFile, File
import pandas as pd
from db import get_connection
import io

app = FastAPI()

conn = get_connection()

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

    conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")

    metadata = f"Table {table_name}\n"
    metadata += f"Columns:\n"
    for col, dtype in df.dtypes.items():
        metadata += f" - {col}: {dtype}\n"
    metadata += f"Row count: {len(df)}\n"

    return {
        "message": f"Uploaded {file.filename} successfully",
        "table": table_name,
        "metadata": metadata,
        "sample_rows": df.head().to_dict(orient="records")
    }
