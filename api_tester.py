from openai import OpenAI
from src import config

client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL) 
r = client.chat.completions.create( model=config.DEFAULT_MODEL, 
messages=[{"role": "user", "content": "ping"}], 
temperature=0.2 ) 
print("OK:", r.choices[0].message.content)