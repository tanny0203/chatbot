from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def home():
    return {"Hello": "World"}


@app.post("/nl2sql")
async def nl2sql(query: str):
    return {"SQL": f"SELECT * FROM table WHERE column = {query}"}