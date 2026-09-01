async function apiFetch(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    credentials: "include",
    headers: {
      ...(options.headers || {})
    }
  });

  if (response.status === 401) {
    throw new Error("AUTH_REQUIRED");
  }

  if (response.status === 404) {
    throw new Error("MESSAGE_NOT_FOUND");
  }

  if (!response.ok) {
    throw new Error(
      `Server xatosi: ${response.status}`
    );
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
  return apiFetch(
    `/mcp/messages/${encodeURIComponent(message_id)}`
  );
}

async function markMessageAsRead(message_id) {
  return apiFetch(
    `/mcp/messages/${encodeURIComponent(message_id)}/read`,
    {
      method: "POST"
    }
  );
}

async function replyToMessage(message_id, text) {
  return apiFetch(
    `/mcp/messages/${encodeURIComponent(message_id)}/reply`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text })
    }
  );
}

function handleToolError(error) {
  if (error.message === "AUTH_REQUIRED") {
    return {
      success: false,
      error: "AUTH_REQUIRED",
      message: "Foydalanuvchi tizimga kirmagan."
    };
  }

  if (error.message === "MESSAGE_NOT_FOUND") {
    return {
      success: false,
      error: "MESSAGE_NOT_FOUND",
      message: "Xat topilmadi."
    };
  }

  return {
    success: false,
    error: "BACKEND_ERROR",
    message: error.message || "Serverda xatolik yuz berdi."
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
      "Javob avtomatik ravishda mavjud thread ichiga yuboriladi.",
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

const loadEmailsButton =
  document.getElementById("loadEmailsButton");

const emails =
  document.getElementById("emails");

const status =
  document.getElementById("status");

const messageDetails =
  document.getElementById("messageDetails");

const messageContent =
  document.getElementById("messageContent");

const closeMessageButton =
  document.getElementById("closeMessageButton");

const replyText =
  document.getElementById("replyText");

const replyButton =
  document.getElementById("replyButton");

let currentMessageId = null;

function showStatus(message) {
  status.textContent = message;
  status.classList.remove("hidden");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadEmails() {
  loadEmailsButton.disabled = true;
  showStatus("Xatlar yuklanmoqda...");

  try {
    const messages = await listMessages({
      unread: false,
      max_results: 20
    });

    renderEmails(messages);

    showStatus(
      `${messages.length} ta xat yuklandi.`
    );
  } catch (error) {
    if (error.message === "AUTH_REQUIRED") {
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
    loadEmailsButton.disabled = false;
  }
}

function renderEmails(messages) {
  emails.innerHTML = "";

  if (!messages?.length) {
    emails.innerHTML = `
      <div class="status">
        Xatlar topilmadi.
      </div>
    `;

    return;
  }

  for (const message of messages) {
    const element = document.createElement("article");

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

    emails.appendChild(element);
  }
}

async function openMessage(messageId) {
  currentMessageId = messageId;

  messageDetails.classList.remove("hidden");

  messageContent.innerHTML = `
    <p>Xat yuklanmoqda...</p>
  `;

  try {
    const message =
      await getMessageDetail(messageId);

    messageContent.innerHTML = `
      <h2 class="message-subject">
        ${escapeHtml(message.subject)}
      </h2>

      <div class="message-meta">
        <div>
          <strong>Kimdan:</strong>
          ${escapeHtml(message.from)}
        </div>

        <div>
          <strong>Sana:</strong>
          ${escapeHtml(message.date)}
        </div>
      </div>

      <div class="message-body">
        ${escapeHtml(message.body)}
      </div>
    `;

    replyText.value = "";

    if (message.unread) {
      await markMessageAsRead(messageId);
    }
  } catch (error) {
    messageContent.innerHTML = `
      <p>Xatni yuklashda xatolik yuz berdi.</p>
    `;
  }
}

async function sendReply() {
  if (!currentMessageId) {
    return;
  }

  const text = replyText.value.trim();

  if (!text) {
    showStatus("Javob matnini kiriting.");
    return;
  }

  replyButton.disabled = true;

  try {
    const result = await replyToMessage(
      currentMessageId,
      text
    );

    showStatus(
      result.message || "Javob yuborildi."
    );

    replyText.value = "";
  } catch (error) {
    if (error.message === "AUTH_REQUIRED") {
      showStatus(
        "Sessiya tugagan. Google orqali qayta kiring."
      );
    } else {
      showStatus(
        "Javob yuborishda xatolik yuz berdi."
      );
    }
  } finally {
    replyButton.disabled = false;
  }
}

function closeMessage() {
  messageDetails.classList.add("hidden");
  messageContent.innerHTML = "";
  replyText.value = "";
  currentMessageId = null;
}

loadEmailsButton.addEventListener(
  "click",
  loadEmails
);

closeMessageButton.addEventListener(
  "click",
  closeMessage
);

replyButton.addEventListener(
  "click",
  sendReply
);

registerWebMCPTools();
