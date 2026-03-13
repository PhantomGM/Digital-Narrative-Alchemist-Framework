import os
from ollama import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')}
)

messages = [
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
]

print("Sending request to Ollama Cloud...")
try:
    for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
      print(part['message']['content'], end='', flush=True)
    print("\n\nSuccess!")
except Exception as e:
    print(f"\nError: {e}")
