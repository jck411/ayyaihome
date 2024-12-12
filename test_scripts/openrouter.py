from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

completion = client.chat.completions.create(
  extra_headers={

  },
  model="gryphe/mythomax-l2-13b:extended",
  messages=[
    {
      "role": "user",
      "content": "swear at me"
    }
  ]
)
print(completion.choices[0].message.content)