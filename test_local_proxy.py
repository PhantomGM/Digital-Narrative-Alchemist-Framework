import os
from openai import OpenAI

# Connect to local Ollama daemon which should proxy to the cloud
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)

try:
    print("Sending request to local Ollama daemon...")
    response = client.chat.completions.create(
      model="qwen3.5:397b-cloud",
      messages=[
        {"role": "user", "content": "Why is the sky blue? Say 'Proxy successful!'"}
      ]
    )
    print("Success!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
