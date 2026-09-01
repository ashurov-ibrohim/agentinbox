# AgentInbox Backend — WebMCP uchun API hujjati

Bu hujjat frontend/WebMCP tomonidan chaqiriladigan endpointlarni tavsiflaydi. Sherigingiz `document.modelContext.registerTool()` orqali ro'yxatdan o'tkazgan har bir tool'ning `execute` funksiyasi ichida shu endpointlarga oddiy `fetch()` so'rovi yuboradi — boshqa hech narsa kerak emas.

## Base URL

- Local development: `http://localhost:8000`
- Production (frontend backend bilan bitta serverda, `backend/static` orqali serve qilinganda): **relative URL** ishlating — masalan `fetch("/mcp/messages", ...)`. Bitta origin bo'lgani uchun `credentials: "include"` shart emas, lekin xavfsizlik uchun qoldirish mumkin.

## Autentifikatsiya (juda muhim)

Auth cookie orqali ishlaydi, Authorization header orqali emas:

1. Foydalanuvchi avval `GET /auth/login` ga o'tadi (Google login boshlanadi)
2. Google consent'dan keyin `GET /auth/callback` chaqiriladi, backend HttpOnly `access_token` cookie'sini o'rnatadi
3. Shundan keyingi barcha `/mcp/*` so'rovlar shu cookie orqali avtomatik autentifikatsiya qilinadi

**Frontend tomonidan `fetch()` chaqirayotganda har doim `credentials: "include"` qo'shish shart** (local development'da, alohida portlarda ishlaganda), aks holda cookie yuborilmaydi:

```js
fetch("http://localhost:8000/mcp/messages", {
  credentials: "include"
})
```

Agar frontend va backend boshqa-boshqa portlarda ishlasa (masalan frontend `:3000`, backend `:8000`), backend `main.py`dagi CORS sozlamasida frontend URL `FRONTEND_URL` orqali ruxsat berilgan bo'lishi kerak — bu allaqachon sozlangan. Agar login qilinmagan bo'lsa, quyidagi endpointlar `401 Unauthorized` qaytaradi.

---

## 1. Xatlar ro'yxatini olish

```
GET /mcp/messages?unread=true&max_results=10
```

Query parametrlari (ikkalasi ham ixtiyoriy):
- `unread` (bool, default `false`) — `true` bo'lsa faqat o'qilmagan xatlar
- `max_results` (int, default `10`) — nechta xat qaytarilishi

**Response** `200 OK`:
```json
[
  { "id": "18f2a3b...", "threadId": "18f2a3b..." },
  { "id": "18f2a3c...", "threadId": "18f2a3c..." }
]
```

Bu yerda faqat ID'lar qaytadi — xat mazmunini olish uchun (2)-endpoint kerak.

---

## 2. Bitta xatning to'liq mazmuni

```
GET /mcp/messages/{message_id}
```

**Response** `200 OK`:
```json
{
  "id": "18f2a3b...",
  "thread_id": "18f2a3b...",
  "subject": "Meeting tomorrow",
  "from": "someone@example.com",
  "date": "Sun, 31 Aug 2026 10:00:00 +0500",
  "snippet": "Hi, just confirming...",
  "body": "Hi,\n\nJust confirming our meeting tomorrow at 10am.\n\nBest,\nJohn",
  "unread": true
}
```

---

## 3. Xatni "o'qilgan" deb belgilash

```
POST /mcp/messages/{message_id}/read
```

Body kerak emas.

**Response** `200 OK`:
```json
{ "message": "Xat o'qilgan deb belgilandi" }
```

---

## 4. Xatga javob yozib yuborish

```
POST /mcp/messages/{message_id}/reply
Content-Type: application/json
```

**Request body**:
```json
{ "text": "Rahmat, ertaga ko'rishguncha!" }
```

**Response** `200 OK`:
```json
{ "message": "Javob yuborildi", "sent_id": "18f2a3d..." }
```

Bu original xatning `threadId` va `In-Reply-To`/`References` headerlarini avtomatik to'g'ri qo'yadi — javob Gmail'da to'g'ri thread ichida ko'rinadi.

---

## Xatolar

Har bir endpoint quyidagi holatlarda xato qaytarishi mumkin:

| Status | Sabab |
|---|---|
| `401` | Foydalanuvchi login qilmagan yoki cookie eskirgan — `/auth/login`ga qaytarish kerak |
| `404` | Berilgan `message_id` topilmadi |
| `500` | Backend/Gmail API tomonidagi kutilmagan xato |

---

## WebMCP tool ro'yxatdan o'tkazishga misol

```js
document.modelContext.registerTool({
  name: "list_unread_emails",
  description: "Foydalanuvchining o'qilmagan Gmail xatlarini qaytaradi",
  inputSchema: { type: "object", properties: {} },
  execute: async () => {
    const res = await fetch("/mcp/messages?unread=true", {
      credentials: "include"
    });
    return await res.json();
  }
});

document.modelContext.registerTool({
  name: "reply_to_email",
  description: "Berilgan xatga javob yozib yuboradi",
  inputSchema: {
    type: "object",
    properties: {
      message_id: { type: "string" },
      text: { type: "string" }
    },
    required: ["message_id", "text"]
  },
  execute: async ({ message_id, text }) => {
    const res = await fetch(`/mcp/messages/${message_id}/reply`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    return await res.json();
  }
});
```

Xuddi shu naqsh qolgan ikkita endpoint (`get_message_detail`, `mark_as_read`) uchun ham ishlatiladi.
