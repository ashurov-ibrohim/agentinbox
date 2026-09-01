import base64
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from models.user import Users
from config import settings
from constants import get_scopes


def get_gmail_service(user: Users):
    access_token = user.access_token
    refresh_token = user.refresh_token

    credential = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=get_scopes(),
    )

    return build("gmail", "v1", credentials=credential)


def list_messages(user: Users, max_results: int = 10, unread_only: bool = False):
    service = get_gmail_service(user)

    # Gmail'ning o'zining qidiruv operatorlaridan foydalanamiz (Gmail interfeysidagi
    # qidiruv qatoriga yozadigan narsalaringiz bilan bir xil, masalan "is:unread")
    query = "is:unread" if unread_only else None

    response = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results, q=query)
        .execute()
    )

    return response.get("messages", [])


def _decode_base64url(data: str) -> str:
    """Gmail API xat matnini base64url formatida qaytaradi - buni oddiy matnga aylantiradi."""
    decoded_bytes = base64.urlsafe_b64decode(data.encode("ASCII"))
    return decoded_bytes.decode("utf-8", errors="replace")


def _extract_body(payload: dict) -> str:
    """
    Xat matnini 'payload' strukturasidan qidirib topadi.

    Gmail xabari 2 xil ko'rinishda bo'lishi mumkin:
    1. Oddiy xat - matn to'g'ridan-to'g'ri payload["body"]["data"]da
    2. Multipart xat (matn + HTML, yoki qo'shimchali) - matn payload["parts"]
       ro'yxati ichida, har bir "part" o'zining mimeType'iga ega
    """
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    # 1-holat: oddiy, bo'linmagan xat
    if mime_type == "text/plain" and body_data:
        return _decode_base64url(body_data)

    plain_text = None
    html_text = None

    # 2-holat: multipart - har bir qismni aylanib chiqamiz
    for part in payload.get("parts", []) or []:
        part_mime = part.get("mimeType", "")
        part_data = part.get("body", {}).get("data")

        if part_mime == "text/plain" and part_data:
            plain_text = _decode_base64url(part_data)
        elif part_mime == "text/html" and part_data:
            html_text = _decode_base64url(part_data)
        elif part.get("parts"):
            # Ichma-ich multipart (masalan multipart/mixed ichida yana
            # multipart/alternative bo'lishi mumkin) - rekursiv qidiramiz
            nested = _extract_body(part)
            if nested and not plain_text:
                plain_text = nested

    # Ustuvorlik: avval plain text, topilmasa HTML, undan ham topilmasa bo'sh
    return plain_text or html_text or ""


def get_message_detail(user: Users, message_id: str) -> dict:
    """Bitta xatning to'liq ma'lumotini (kimdan, mavzu, matn, o'qilganmi) qaytaradi."""
    service = get_gmail_service(user)

    message = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )

    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    # Headerlar [{"name": "Subject", "value": "..."}] ko'rinishida ro'yxat bo'lib
    # keladi - qulay bo'lishi uchun dictionary'ga aylantiramiz
    header_map = {h["name"]: h["value"] for h in headers}

    label_ids = message.get("labelIds", [])

    return {
        "id": message.get("id"),
        "thread_id": message.get("threadId"),
        "subject": header_map.get("Subject", "(mavzu yo'q)"),
        "from": header_map.get("From", ""),
        "date": header_map.get("Date", ""),
        "snippet": message.get("snippet", ""),
        "body": _extract_body(payload),
        "unread": "UNREAD" in label_ids,
    }


def mark_as_read(user: Users, message_id: str) -> dict:
    """Xatni 'o'qilgan' deb belgilaydi - Gmail'dagi UNREAD labelini olib tashlaydi."""
    service = get_gmail_service(user)

    return (
        service.users()
        .messages()
        .modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        )
        .execute()
    )


def send_reply(user: Users, message_id: str, reply_text: str) -> dict:
    """
    Berilgan xatga javob yozib yuboradi. Gmail API'da tayyor "reply" funksiyasi
    yo'q - o'zimiz to'g'ri formatlangan email xabar (MIME) yasab, uni thread'ga
    bog'lab yuborishimiz kerak.
    """
    service = get_gmail_service(user)

    # 1-qadam: asl xatning kerakli header'larini olamiz (to'liq xatni emas,
    # faqat metadata - bu tezroq va bizga ko'proq narsa kerak emas)
    original = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=["Subject", "From", "Message-ID"],
        )
        .execute()
    )
    headers = {
        h["name"]: h["value"] for h in original.get("payload", {}).get("headers", [])
    }

    to_address = headers.get("From", "")
    original_message_id = headers.get("Message-ID", "")

    subject = headers.get("Subject", "")
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    # 2-qadam: standart Python email kutubxonasi bilan MIME xabar yasaymiz
    mime_message = MIMEText(reply_text)
    mime_message["To"] = to_address
    mime_message["Subject"] = subject
    if original_message_id:
        # Bular email mijozlariga (Gmail, Outlook) "bu xat avvalgisiga javob"
        # ekanini bildiradigan standart header'lar - shu tufayli xatlar bitta
        # suhbat (thread) sifatida ko'rinadi
        mime_message["In-Reply-To"] = original_message_id
        mime_message["References"] = original_message_id

    # 3-qadam: Gmail API xom (raw) email xabarni ham base64url formatida kutadi
    raw_bytes = mime_message.as_bytes()
    raw_encoded = base64.urlsafe_b64encode(raw_bytes).decode("ascii")

    # threadId'ni ham berish - shu tufayli javobimiz asl xat bilan bitta
    # suhbat (thread) sifatida guruhlanadi
    return (
        service.users()
        .messages()
        .send(
            userId="me",
            body={"raw": raw_encoded, "threadId": original.get("threadId")},
        )
        .execute()
    )
