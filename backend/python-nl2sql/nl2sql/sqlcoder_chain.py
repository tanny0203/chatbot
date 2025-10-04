from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from prompt_template import SQLCODER_PROMPT
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
        Each column entry includes: name, data_type, sql_type, nullability, enums/top values,
        mappings, synonyms, and a short description.
        """
        def short_list(values, max_items=5):
            if not values:
                return []
            return values[:max_items]

        lines = []
        for col in columns_metadata:
            name = col.get("column_name")
            dtype = col.get("data_type")
            sql_type = col.get("sql_type")
            nullable = col.get("nullable")
            is_cat = col.get("is_category")
            is_bool = col.get("is_boolean")
            is_date = col.get("is_date")
            enum_values = short_list(col.get("enum_values") or [])
            top_values = short_list(col.get("top_values") or [])
            sample_values = short_list(col.get("sample_values") or [])
            value_mappings = col.get("value_mappings") or {}
            synonym_mappings = col.get("synonym_mappings") or {}
            description = col.get("description", "")

            parts = [
                f"- {name} [{dtype} -> {sql_type}]",
                f"  nullable: {nullable}, category: {is_cat}, boolean: {is_bool}, date: {is_date}",
            ]

            if enum_values:
                parts.append(f"  enum_values: {enum_values}")
            if top_values:
                parts.append(f"  top_values: {top_values}")
            if sample_values:
                parts.append(f"  sample: {sample_values}")
            if value_mappings:
                parts.append(f"  value_mappings: {value_mappings}")
            if synonym_mappings:
                # Only include synonyms relevant to this column
                syns = synonym_mappings.get(name) if isinstance(synonym_mappings, dict) else None
                if syns:
                    parts.append(f"  synonym_mappings: {syns}")
            if description:
                parts.append(f"  description: {description}")

            lines.append("\n".join(parts))

        return "\n".join(lines)

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

        return result