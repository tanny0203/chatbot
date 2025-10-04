from langchain.prompts import PromptTemplate

# Template for SQLCoder model
SQLCODER_PROMPT = PromptTemplate(
    input_variables=["table_name", "columns", "user_query"],
    template=(
        "You are an expert PostgreSQL analyst and SQL query generator.\n"
        "Use the provided table metadata to compose a single, correct SQL query that answers the user's question.\n\n"
        "### Table Name\n"
        "{table_name}\n\n"
        "### Columns and Metadata\n"
        "(Use names exactly as given; they are already cleaned for PostgreSQL)\n"
        "{columns}\n\n"
        "### Rules\n"
        "- Output only SQL (no explanation or markdown).\n"
        "- Use standard PostgreSQL syntax.\n"
        "- Do not invent column names or values beyond the metadata.\n"
        "- Prefer ILIKE for case-insensitive text searches.\n"
        "- When grouping, select only grouped columns and aggregates.\n"
        "- Use LIMIT when returning raw rows (defaults to 50 if not specified by the question).\n"
        "- Use value_mappings and synonym_mappings to interpret category codes or alternate phrasings if applicable.\n"
        "- Quote identifiers with double quotes if needed.\n\n"
        "### User Question\n"
        "{user_query}\n\n"
        "### SQL Query:"
    ),
)