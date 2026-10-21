
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors

# Find project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load API key from .env
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY was not found. Check your .env file."
    )

client = genai.Client(api_key=API_KEY)

print("API key loaded successfully.")
print("\nChecking available Gemini models...\n")

# Find models that support text generation
available_models = []

try:
    for model in client.models.list():
        name = model.name or ""
        actions = model.supported_actions or []

        if "gemini" in name.lower() and "generateContent" in actions:
            available_models.append(name)
            print(name)

except Exception as error:
    print("Failed to list models:", error)
    raise

if not available_models:
    raise RuntimeError("No text-generation Gemini models found.")

# Prefer Google's suggested model if available.
preferred = "models/gemini-3.8-flash"

MODEL = (
    preferred
    if preferred in available_models
    else available_models[0]
)

print(f"\nTesting model: {MODEL}")

try:
    response = client.models.generate_content(
        model=MODEL,
        contents="Say hello in one short sentence."
    )

    answer = (response.text or "").strip()

    if not answer:
        print("Gemini returned an empty response.")
    else:
        print("\nGEMINI RESPONSE:")
        print(answer)
        print("\nSUCCESS!")
        print("Working model:", MODEL)
        print("Add this model name to your .env file.")

except errors.ServerError as error:
    print("\nGemini server error:", error)
    print("The model may be temporarily overloaded.")

except errors.ClientError as error:
    print("\nGemini API error:", error)
    print("Check the selected model, access and quota.")
