import openai  # or watsonx / any LLM API

def chat_llm(system_prompt: str, user_prompt: str) -> str:
    # pseudo-code – adapt to your provider
    resp = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    return resp["choices"][0]["message"]["content"]
# LLM interactions