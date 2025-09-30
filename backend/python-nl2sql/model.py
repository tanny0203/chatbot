from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate


llm = Ollama(model="llama2")  

prompt = PromptTemplate(
    input_variables=["question"],
    template="Convert the following natural language question to SQL: {question}"
)

# Create the chain
chain = LLMChain(llm=llm, prompt=prompt)

# Example usage
def nl2sql(question: str) -> str:
    result = chain.run(question=question)
    return result

# Example
if __name__ == "__main__":
    question = "Show me all users who registered in 2023."
    sql_query = nl2sql(question)
    print(sql_query)