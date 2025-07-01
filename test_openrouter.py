#!/usr/bin/env python3

from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

try:
    completion = client.chat.completions.create(
      extra_headers={
        "HTTP-Referer": "https://hospital-booking-system.com",
        "X-Title": "Hospital AI Test",
      },
      model="deepseek/deepseek-r1-0528:free",
      messages=[
        {
          "role": "user",
          "content": "What is the meaning of life? Answer in one sentence."
        }
      ]
    )
    print("SUCCESS!")
    print(completion.choices[0].message.content)
except Exception as e:
    print("ERROR:")
    print(str(e))