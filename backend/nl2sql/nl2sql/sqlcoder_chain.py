from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from .prompt_template import SQLCODER_PROMPT
import json

class NL2SQLGenerator:
    def __init__(self, model_name: str = "sqlcoder:7b"):
        """
        Initialize SQLCoder model via Ollama backend.
        """
        self.llm = ChatOllama(
            model=model_name,
            temperature=0.0,
            top_p=0.9,
            num_predict=512
        )
        self.chain = SQLCODER_PROMPT | self.llm | StrOutputParser()

    def format_metadata(self, columns_metadata: list[dict]) -> str:
        """
        Format the metadata list into readable text for the model.
        Each column entry should contain name, data_type, example, and description.
        """
        formatted = []
        for col in columns_metadata:
            entry = (
                f"- {col['column_name']} ({col['data_type']}) "
                f"→ description: {col.get('description', 'N/A')}, "
                f"sample: {col.get('sample_values', [])}"
            )
            formatted.append(entry)
        return "\n".join(formatted)

    async def generate_sql(self, table_name: str, metadata: list[dict], user_query: str) -> str:
        """
        Given user query + metadata, return generated SQL string.
        """
        columns_text = self.format_metadata(metadata)
        result = await self.chain.ainvoke({
            "table_name": table_name,
            "columns": columns_text,
            "user_query": user_query
        })

        sql_text = result["text"].strip()
        # Optional: Basic cleanup
        sql_text = sql_text.replace("```sql", "").replace("```", "").strip()
        return sql_text
