from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm = ChatOpenAI(
    model="qwen3.5:397b-cloud",
    temperature=0.1,
    api_key="ollama",
    base_url="http://localhost:11434/v1",
    max_retries=0
)

print("Sending Langchain ChatOpenAI request...")
try:
    response = llm.invoke([HumanMessage(content="Why is the sky blue?")])
    print("Success!")
    print(response.content)
except Exception as e:
    print(f"Error: {e}")
