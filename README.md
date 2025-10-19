# 📱 WhatsApp Message Reader

Simple WhatsApp webhook receiver that **logs all incoming messages to console and stores them in PostgreSQL**.

---

## Features
- 📥 Receives WhatsApp webhooks from `go-whatsapp-web-multidevice`
- 📝 Logs message contents to console
- 💾 Stores all messages in PostgreSQL database
- 🔗 Support for multiple message types (text, media, links)
- ⚡ REST API with Swagger docs (`localhost:8000/docs`)

---

## 📋 Prerequisites

- 🐳 Docker and Docker Compose  
- 🐍 Python 3.12+  
- 🗄️ PostgreSQL with `pgvector` extension  
- 🔑 Voyage AI API key  
- 📲 WhatsApp account for the bot 


## Quick Start

### 1. Clone & Configure

`git clone https://github.com/YOUR_USER/wa_llm.git
cd wa_llm`

### 2. Create .env file

Create a `.env` file in the src directory with the following variables:

```env
WHATSAPP_HOST=http://localhost:3003
WHATSAPP_BASIC_AUTH_USER=admin
WHATSAPP_BASIC_AUTH_PASSWORD=admin
DB_URI=postgresql+asyncpg://user:password@localhost:5433/postgres
LOG_LEVEL=INFO
```

#### Environment Variables

| Variable                       | Description                          | Default                                                      |
| ------------------------------ | ------------------------------------ | ------------------------------------------------------------ |
| `WHATSAPP_HOST`                | WhatsApp Web API URL                 | `http://localhost:3003`                                      |
| `WHATSAPP_BASIC_AUTH_USER`     | WhatsApp API user                    | `admin`                                                      |
| `WHATSAPP_BASIC_AUTH_PASSWORD` | WhatsApp API password                | `admin`                                                      |
| `DB_URI`                       | PostgreSQL URI                       | `postgresql+asyncpg://user:password@localhost:5433/postgres` |
| `LOG_LEVEL`                    | Log level (`DEBUG`, `INFO`, `ERROR`) | `INFO`                                                       |

### 3. starting the services
```docker compose up -d```

### 4. Connect your device
1. Open http://localhost:3003
2. Scan the QR code with your WhatsApp mobile app.
3. Invite the bot device to any target groups you want to monitor.
4. Restart service: `docker compose restart web-server`

### 5. Monitor Messages
The app will automatically:
- Log all incoming WhatsApp messages to the console
- Store messages in the PostgreSQL database
- Handle all message types (text, media, contacts, etc.)

### 6. API usage
Swagger docs available at: `http://localhost:3003/docs`

#### Key Endpoints
* <b>/webhook (POST)</b> Receives WhatsApp webhooks and processes messages
* <b>/status (GET)</b> Health check endpoint

---
## Developing
* install uv tools `uv sync --all-extras --active`
* run ruff (Python linter and code formatter) `ruff check` and `ruff format`
* check for types usage `pyright`

### Key Files

- Main application: `app/main.py`
- WhatsApp client: `src/whatsapp/client.py`
- Message handler: `src/handler/__init__.py`
- Database models: `src/models/`

---

## Architecture

The project consists of several key components:

- FastAPI backend for webhook handling
- WhatsApp Web API service for receiving messages
- PostgreSQL database for message storage
- Console logging for message monitoring

---
## Contributing
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---
## License
[LICENCE](CODE_OF_CONDUCT.md)