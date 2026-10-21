
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic, AnthropicError

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env", override=True)

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")

if not API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY missing from .env"
    )

client = Anthropic(
    api_key=API_KEY,
    timeout=60.0,
    max_retries=1
)

print(f"Testing Claude: {MODEL}")

start = time.perf_counter()

try:
    response = client.messages.create(
        model=MODEL,
        max_tokens=150,
        messages=[
            {
                "role": "user",
                "content": (
                    "Hello! Explain what a Master's "
                    "degree is in two sentences."
                )
            }
        ]
    )

    answer = "\n".join(
        block.text
        for block in response.content
        if block.type == "text"
    )

    print("\nCLAUDE RESPONSE:\n")
    print(answer)

    print(
        "\nResponse time:",
        round(time.perf_counter() - start, 2),
        "seconds"
    )

    print("Input tokens:", response.usage.input_tokens)
    print("Output tokens:", response.usage.output_tokens)

except AnthropicError as error:
    print("\nClaude API error:")
    print(error)
