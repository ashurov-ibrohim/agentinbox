from typing import List, Optional

from google import genai
from google.genai import types

from config import settings
from models.user import Users
from services.gmail_services import (
    list_messages,
    get_message_detail,
    mark_as_read,
    send_reply,
)

MODEL_NAME = "gemini-3.7-flash"

client = genai.Client(api_key=settings.GEMINI_API_KEY)


# --- Tool e'lonlari: Gemini'ga qaysi funksiyalarni "ko'rsatishimiz" kerakligi ---

LIST_MESSAGES_TOOL = {
    "name": "list_messages",
    "description": "Foydalanuvchining Gmail pochta qutisidagi xatlar ro'yxatini qaytaradi (faqat ID'lar).",
    "parameters": {
        "type": "object",
        "properties": {
            "unread_only": {
                "type": "boolean",
                "description": "True bo'lsa, faqat o'qilmagan xatlarni qaytaradi",
            },
            "max_results": {
                "type": "integer",
                "description": "Nechta xat qaytarilishi kerak (standart: 10)",
            },
        },
        "required": [],
    },
}

GET_MESSAGE_DETAIL_TOOL = {
    "name": "get_message_detail",
    "description": "Bitta xatning to'liq mazmunini (kimdan, mavzu, matn, o'qilganmi) qaytaradi.",
    "parameters": {
        "type": "object",
        "properties": {
            "message_id": {"type": "string", "description": "Xatning Gmail ID'si"},
        },
        "required": ["message_id"],
    },
}

MARK_AS_READ_TOOL = {
    "name": "mark_as_read",
    "description": "Xatni o'qilgan deb belgilaydi.",
    "parameters": {
        "type": "object",
        "properties": {
            "message_id": {"type": "string", "description": "Xatning Gmail ID'si"},
        },
        "required": ["message_id"],
    },
}

SEND_REPLY_TOOL = {
    "name": "send_reply",
    "description": "Berilgan xatga javob yozib yuboradi.",
    "parameters": {
        "type": "object",
        "properties": {
            "message_id": {
                "type": "string",
                "description": "Javob yoziladigan xatning Gmail ID'si",
            },
            "reply_text": {"type": "string", "description": "Javob matni"},
        },
        "required": ["message_id", "reply_text"],
    },
}

# Tool nomini haqiqiy Python funksiyasiga bog'laydigan lug'at
TOOL_FUNCTIONS = {
    "list_messages": list_messages,
    "get_message_detail": get_message_detail,
    "mark_as_read": mark_as_read,
    "send_reply": send_reply,
}


def _build_tool_config() -> types.GenerateContentConfig:
    declarations = [
        LIST_MESSAGES_TOOL,
        GET_MESSAGE_DETAIL_TOOL,
        MARK_AS_READ_TOOL,
        SEND_REPLY_TOOL,
    ]
    tool = types.Tool(function_declarations=declarations)
    return types.GenerateContentConfig(tools=[tool])


def _execute_tool(user: Users, tool_name: str, arguments: dict):
    """Gemini chaqirgan tool nomini haqiqiy funksiyaga bog'lab, natijasini qaytaradi."""
    func = TOOL_FUNCTIONS.get(tool_name)
    if not func:
        return {"error": f"Noma'lum tool: {tool_name}"}

    # Har bir gmail_services funksiyasi birinchi argument sifatida 'user'ni kutadi,
    # lekin Gemini 'user' haqida bilmaydi (xavfsizlik uchun ataylab shunday) -
    # shuning uchun uni o'zimiz qo'shib beramiz
    return func(user, **arguments)


def chat_with_agent(
    user: Users, message: str, history: Optional[List[dict]] = None
) -> dict:
    """
    Foydalanuvchi xabarini Gemini'ga yuboradi. 'history' - shu sessiyada avval
    yozilgan xabarlar ({"role": "user"/"model", "content": "..."} ko'rinishida),
    suhbat kontekstini davom ettirish uchun. Agar Gemini biror tool chaqirishni
    xohlasa, uni avtomatik bajaramiz va natijani qaytarib, yakuniy javobni olamiz.
    """
    config = _build_tool_config()

    contents = []
    for turn in history or []:
        role = "model" if turn["role"] == "model" else "user"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=turn["content"])])
        )
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    response = client.models.generate_content(
        model=MODEL_NAME, contents=contents, config=config
    )

    # Gemini bir nechta tool'ni ketma-ket chaqirishi mumkin - shuning uchun
    # function_call kelmay qolguncha davom etamiz
    while True:
        part = response.candidates[0].content.parts[0]
        function_call = getattr(part, "function_call", None)
        if not function_call:
            break

        result = _execute_tool(user, function_call.name, dict(function_call.args))

        function_response_part = types.Part.from_function_response(
            name=function_call.name,
            response={"result": result},
        )

        contents.append(response.candidates[0].content)
        contents.append(types.Content(role="user", parts=[function_response_part]))

        response = client.models.generate_content(
            model=MODEL_NAME, contents=contents, config=config
        )

    return {"reply": response.text}
