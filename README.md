# AgentInbox

An AI-agent-powered Gmail manager built on **WebMCP**. It lets a browser-native AI agent find important emails, filter unread ones, and send replies on the user's behalf.

Built for the [WebMCP Challenge](https://webmcphack.devpost.com/) hackathon.

## Why WebMCP?

Most AI email assistants run their own LLM orchestration on the backend. AgentInbox instead exposes page-level actions directly to the browser's own AI agent via **WebMCP** (`document.modelContext.registerTool()`) — the agent the user already trusts (ChatGPT Atlas, or Chrome's built-in agent mode) drives Gmail within the user's own authenticated session. The backend doesn't reimplement an LLM; it exposes a small, authenticated, well-tested set of REST actions for that agent to call.

## Architecture

```
routers → services → repos → models   (SQLAlchemy 2.0, PostgreSQL)
```

- **Auth**: Google OAuth2 login, JWT (HttpOnly cookie)
- **Gmail integration**: list messages, get message detail, mark as read, reply within the correct thread (`In-Reply-To`/`References`)
- **WebMCP REST API** (`/mcp/*`): 4 authenticated endpoints called by the browser agent — full reference: [`WEBMCP_API.md`](WEBMCP_API.md)

## Stack

FastAPI · PostgreSQL + SQLAlchemy 2.0 · Google OAuth2 · JWT · Gmail API

## Running locally

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # fill in the values
uvicorn main:app --reload
```

Swagger UI: `http://localhost:8000/docs`

## Live demo

<!-- TODO: add the live URL once deployed to Render -->

## License

[MIT](LICENSE)
