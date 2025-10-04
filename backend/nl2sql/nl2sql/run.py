from sqlcoder_chain import NL2SQLGenerator
from nl2sql.sqlcoder_chain import NL2SQLGenerator
import asyncio

async def test():
    # Mock metadata
    metadata = [
        {
            "column_name": "student_name",
            "data_type": "TEXT",
            "description": "Name of the student",
            "sample_values": ["Alice", "Bob", "Charlie"]
        },
        {
            "column_name": "math_marks",
            "data_type": "INTEGER",
            "description": "Marks scored in mathematics",
            "sample_values": [95, 88, 72]
        }
    ]

    nl2sql = NL2SQLGenerator("sqlcoder:7b")
    query = await nl2sql.generate_sql(
        table_name="students_marks",
        metadata=metadata,
        user_query="Find top 5 students with highest math marks"
    )

    print("Generated SQL:\n", query)

asyncio.run(test())
