const API_BASE_URL = "http://localhost:8000";

async function apiFetch(path, options = {}) {
const response = await fetch(`${API_BASE_URL}${path}`, {
...options,
credentials: "include",
headers: {
...(options.headers || {})
}
});

if (response.status === 401) {
const error = new Error("AUTH_REQUIRED");
error.code = "AUTH_REQUIRED";
throw error;
}

if (response.status === 404) {
const error = new Error("MESSAGE_NOT_FOUND");
error.code = "MESSAGE_NOT_FOUND";
throw error;
}

if (!response.ok) {
const text = await response.text();
const error = new Error(
text || `Server xatosi: ${response.status}`
);
error.code = "BACKEND_ERROR";
error.status = response.status;
throw error;
}

return response.json();
}

async function listMessages({
unread = false,
max_results = 10
} = {}) {
const params = new URLSearchParams({
unread: String(unread),
max_results: String(max_results)
});

return apiFetch(`/mcp/messages?${params}`);
}

async function getMessageDetail(message_id) {
if (!message_id) {
throw new Error("message_id kiritilishi kerak");
}

return apiFetch(
`/mcp/messages/${encodeURIComponent(message_id)}`
);
}

async function markMessageAsRead(message_id) {
if (!message_id) {
throw new Error("message_id kiritilishi kerak");
}

return apiFetch(
`/mcp/messages/${encodeURIComponent(message_id)}/read`,
{
method: "POST"
}
);
}

async function replyToMessage(message_id, text) {
if (!message_id) {
throw new Error("message_id kiritilishi kerak");
}

if (!text || !text.trim()) {
throw new Error("Javob matni bo‘sh bo‘lishi mumkin emas");
}

return apiFetch(
`/mcp/messages/${encodeURIComponent(message_id)}/reply`,
{
method: "POST",
headers: {
"Content-Type": "application/json"
},
body: JSON.stringify({
text: text.trim()
})
}
);
}

function handleToolError(error) {
if (error?.code === "AUTH_REQUIRED") {
return {
success: false,
error: "AUTH_REQUIRED",
message: "Foydalanuvchi tizimga kirmagan."
};
}

if (error?.code === "MESSAGE_NOT_FOUND") {
return {
success: false,
error: "MESSAGE_NOT_FOUND",
message: "Xat topilmadi."
};
}

return {
success: false,
error: "BACKEND_ERROR",
message:
error?.message ||
"Serverda xatolik yuz berdi."
};
}

function registerWebMCPTools() {
if (
!document.modelContext ||
typeof document.modelContext.registerTool !== "function"
) {
return;
}

document.modelContext.registerTool({
name: "list_emails",
description:
"Foydalanuvchining Gmail xatlari ro‘yxatini olish. " +
"Faqat o‘qilmagan xatlarni olish va natijalar sonini belgilash mumkin.",
inputSchema: {
type: "object",
properties: {
unread: {
type: "boolean",
description:
"true bo‘lsa, faqat o‘qilmagan xatlar qaytariladi."
},
max_results: {
type: "number",
description:
"Qaytariladigan xatlar maksimal soni."
}
}
},
execute: async ({
unread = false,
max_results = 10
} = {}) => {
try {
return await listMessages({
unread,
max_results
});
} catch (error) {
return handleToolError(error);
}
}
});

document.modelContext.registerTool({
name: "get_message_detail",
description:
"Berilgan message_id orqali Gmail xatining to‘liq mazmunini olish. " +
"Xat mavzusi, yuboruvchi, sana, qisqacha mazmuni, matni va o‘qilganlik holatini qaytaradi.",
inputSchema: {
type: "object",
properties: {
message_id: {
type: "string",
description: "Gmail xatining ID raqami."
}
},
required: ["message_id"]
},
execute: async ({ message_id }) => {
try {
return await getMessageDetail(message_id);
} catch (error) {
return handleToolError(error);
}
}
});

document.modelContext.registerTool({
name: "mark_as_read",
description:
"Berilgan Gmail xatini o‘qilgan deb belgilash.",
inputSchema: {
type: "object",
properties: {
message_id: {
type: "string",
description: "Gmail xatining ID raqami."
}
},
required: ["message_id"]
},
execute: async ({ message_id }) => {
try {
return await markMessageAsRead(message_id);
} catch (error) {
return handleToolError(error);
}
}
});

document.modelContext.registerTool({
name: "reply_to_email",
description:
"Berilgan Gmail xatiga javob yuborish. " +
"Javob avtomatik ravishda xatning mavjud thread'iga yuboriladi.",
inputSchema: {
type: "object",
properties: {
message_id: {
type: "string",
description:
"Javob yuboriladigan Gmail xatining ID raqami."
},
text: {
type: "string",
description:
"Yuboriladigan javob matni."
}
},
required: ["message_id", "text"]
},
execute: async ({
message_id,
text
}) => {
try {
return await replyToMessage(
message_id,
text
);
} catch (error) {
return handleToolError(error);
}
}
});
}

const elements = {
loadEmailsButton:
document.getElementById("loadEmailsButton"),

emails:
document.getElementById("emails"),

status:
document.getElementById("status"),

messageDetails:
document.getElementById("messageDetails"),

messageContent:
document.getElementById("messageContent"),

closeMessageButton:
document.getElementById("closeMessageButton"),

replyText:
document.getElementById("replyText"),

replyButton:
document.getElementById("replyButton")
};

let currentMessageId = null;

function showStatus(message) {
elements.status.textContent = message;
elements.status.classList.remove("hidden");
}

async function loadEmails() {
elements.loadEmailsButton.disabled = true;

showStatus("Xatlar yuklanmoqda...");

try {
const messages = await listMessages({
unread: false,
max_results: 20
});

```
renderEmails(messages);

showStatus(
  `${messages.length} ta xat yuklandi.`
);
```

} catch (error) {
if (error.code === "AUTH_REQUIRED") {
showStatus(
"Tizimga kirilmagan. Google orqali kiring."
);
} else {
showStatus(
error.message ||
"Xatlarni yuklashda xatolik yuz berdi."
);
}
} finally {
elements.loadEmailsButton.disabled = false;
}
}

function renderEmails(messages) {
elements.emails.innerHTML = "";

if (!messages?.length) {
elements.emails.innerHTML = `       <div class="status">
        Xatlar topilmadi.       </div>
    `;

```
return;
```

}

for (const message of messages) {
const element = document.createElement("article");

```
element.className = "email";

element.innerHTML = `
  <div class="email-title">
    Xat
  </div>

  <div class="email-id">
    ID: ${escapeHtml(message.id)}
  </div>

  <div class="email-id">
    Thread: ${escapeHtml(message.threadId)}
  </div>
`;

element.addEventListener(
  "click",
  () => openMessage(message.id)
);

elements.emails.appendChild(element);
```

}
}

async function openMessage(messageId) {
currentMessageId = messageId;

elements.messageDetails.classList.remove(
"hidden"
);

elements.messageContent.innerHTML = `     <p>Xat yuklanmoqda...</p>
  `;

try {
const message =
await getMessageDetail(messageId);

```
renderMessage(message);

if (message.unread) {
  await markMessageAsRead(messageId);
}
```

} catch (error) {
elements.messageContent.innerHTML = `       <p>
        Xatni yuklashda xatolik:
        ${escapeHtml(error.message)}       </p>
    `;
}
}

function renderMessage(message) {
elements.messageContent.innerHTML = ` <h2 class="message-subject">
${escapeHtml(message.subject)} </h2>

```
<div class="message-meta">
  <div>
    <strong>Kimdan:</strong>
    ${escapeHtml(message.from)}
  </div>

  <div>
    <strong>Sana:</strong>
    ${escapeHtml(message.date)}
  </div>

  <div>
    <strong>ID:</strong>
    ${escapeHtml(message.id)}
  </div>
</div>

<div class="message-body">
  ${escapeHtml(message.body)}
</div>
```

`;

elements.replyText.value = "";
}

async function sendReply() {
if (!currentMessageId) {
return;
}

const text =
elements.replyText.value.trim();

if (!text) {
showStatus(
"Javob matnini kiriting."
);

```
return;
```

}

elements.replyButton.disabled = true;

try {
const result =
await replyToMessage(
currentMessageId,
text
);

```
showStatus(
  result.message ||
  "Javob yuborildi."
);

elements.replyText.value = "";
```

} catch (error) {
if (error.code === "AUTH_REQUIRED") {
showStatus(
"Sessiya tugagan. Google orqali qayta kiring."
);
} else {
showStatus(
error.message ||
"Javob yuborishda xatolik yuz berdi."
);
}
} finally {
elements.replyButton.disabled = false;
}
}

function closeMessage() {
elements.messageDetails.classList.add(
"hidden"
);

elements.messageContent.innerHTML = "";

elements.replyText.value = "";

currentMessageId = null;
}

function escapeHtml(value) {
return String(value ?? "")
.replaceAll("&", "&")
.replaceAll("<", "<")
.replaceAll(">", ">")
.replaceAll('"', """)
.replaceAll("'", "'");
}

elements.loadEmailsButton.addEventListener(
"click",
loadEmails
);

elements.closeMessageButton.addEventListener(
"click",
closeMessage
);

elements.replyButton.addEventListener(
"click",
sendReply
);

registerWebMCPTools();
