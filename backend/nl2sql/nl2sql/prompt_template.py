from langchain.prompts import PromptTemplate

# Template for SQLCoder model
SQLCODER_PROMPT = PromptTemplate(
    input_variables=["table_name", "columns", "user_query"],
    template=(
        "You are an expert data analyst and SQL generator.\n"
        "Given the following table structure and metadata, write a valid SQL query that correctly answers the user's question.\n\n"
        "### Table Name:\n{table_name}\n\n"
        "### Columns and Metadata:\n{columns}\n\n"
        "### Rules:\n"
        "- Output only SQL (no explanation or markdown).\n"
        "- Use correct SQL syntax (PostgreSQL).\n"
        "- Never assume column names or data.\n"
        "- Prefer safe aggregation and ordering.\n"
        "- Always use LIMIT when applicable.\n\n"
        "### User Question:\n{user_query}\n\n"
        "### SQL Query:"
    ),
)