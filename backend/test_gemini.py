"""
Gemini API'ni backend'dan tashqarida, alohida sinash uchun.
Ishga tushirish: python test_gemini.py
"""

from google import genai
from config import settings

MODEL_NAME = "gemini-3.7-flash"

print(f"API key boshlanishi: {settings.GEMINI_API_KEY[:10]}...")
print(f"Model: {MODEL_NAME}")
print("-" * 40)

client = genai.Client(api_key=settings.GEMINI_API_KEY)

while True:
    prompt = input("\nPrompt kiriting (chiqish uchun 'exit'): ")
    if prompt.strip().lower() == "exit":
        break

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        print("\n--- Gemini javobi ---")
        print(response.text)
    except Exception as e:
        print("\n--- XATO ---")
        print(f"Turi: {type(e).__name__}")
        print(f"Xabar: {e}")
