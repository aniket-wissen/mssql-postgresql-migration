# MSSQL to PostgreSQL Migration
### Team Setup & Developer Guide

---

## 1. Prerequisites — Tools to Install

| Tool | Purpose | Download |
|---|---|---|
| VS Code | Code editor | https://code.visualstudio.com |
| Docker Desktop | Run databases as containers | https://www.docker.com/products/docker-desktop |
| Python 3.11+ | Run the migration pipeline | https://www.python.org/downloads |
| Git | Clone the project | https://git-scm.com |

---

## 2. Clone the Project

```bash
git clone https://github.com/aniket-wissen/mssql-postgresql-migration.git
cd mssql-postgresql-migration
```

---

## 3. Virtual Environment

A virtual environment keeps project dependencies isolated from your system Python — so packages installed here do not affect other projects on your machine.

```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

> You will see `(venv)` in your terminal when it is active. Always activate before running anything.

---

## 4. Install Dependencies

```bash
pip install pymssql psycopg2-binary python-dotenv groq requests "fastmcp[server]"
```

| Package | Purpose |
|---|---|
| `pymssql` | Connect to SQL Server |
| `psycopg2-binary` | Connect to PostgreSQL |
| `python-dotenv` | Load .env config file |
| `groq` | Connect to Groq AI API |
| `requests` | HTTP calls from MCP client to MCP server |
| `fastmcp[server]` | Run the PostgreSQL MCP server |

---

## 5. Docker — Pull Images

```bash
docker pull mcr.microsoft.com/mssql/server:2022-latest
docker pull postgres:16
```

---

## 6. Docker — Start Containers

```bash
# SQL Server
docker run -d \
  --name sqlserver-local \
  -e ACCEPT_EULA=Y \
  -e SA_PASSWORD=YourStrong@Pass123 \
  -p 1433:1433 \
  mcr.microsoft.com/mssql/server:2022-latest

# PostgreSQL
docker run -d \
  --name postgres-local \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:16
```

Verify both are running:

```bash
docker ps
```

---

## 7. Environment Variables

Create a `.env` file in the project root:

```env
MSSQL_HOST=localhost
MSSQL_PORT=1433
MSSQL_USER=sa
MSSQL_PASSWORD=YourStrong@Pass123
MSSQL_DATABASE=source_db

PG_HOST=localhost
PG_PORT=5433
PG_USER=postgres
PG_PASSWORD=postgres
PG_DATABASE=migrationdb

GROQ_API_KEY=your_groq_api_key_here
```

> **Never commit `.env` to Git.**

---

## 8. Groq API Key

Groq is the free AI service that powers the migration intelligence. (This will be replaced by Claude credentials)

1. Go to https://console.groq.com
2. Sign up for a free account
3. Go to **API Keys** → Create new key
4. Paste the key into `.env` as `GROQ_API_KEY`

---

## 9. Project Structure

```
app/
├── agents/          # AI subagents — each handles one migration task
├── db/              # Database connectors for MSSQL and PostgreSQL
├── mcps/           # MCP server and client for PostgreSQL
├── prompts/         # AI instruction templates sent to Groq
├── skills/          # Reusable utility functions used by agents
├── ai_agent.py      # Groq API connector
├── config.py        # Loads DB config from .env
├── orchestrator.py  # Controls the full migration pipeline
└── main.py          # Entry point — run this to start migration
output/              # Migration reports saved here after each run
```

---

## 10. Agent Descriptions

| Agent | File | What it does |
|---|---|---|
| Orchestrator | `orchestrator.py` | AI decides table migration order, coordinates all agents |
| Schema Agent | `agents/schema_agent.py` | AI converts MSSQL table schema to PostgreSQL DDL |
| Data Agent | `agents/data_agent.py` | AI generates INSERT statements and migrates rows |
| Error Agent | `agents/error_agent.py` | AI analyses failures and suggests fixes |
| Validator | `agents/validator.py` | AI compares row counts and produces a validation report |
| Permissions Agent | `agents/permissions_agent.py` | AI migrates users, roles and grants |

---

## 11. MCP Server

The project uses a **Model Context Protocol (MCP) server** for all PostgreSQL operations. Instead of each agent managing its own database connection, all PostgreSQL operations go through one central MCP server.

```
Agent → MCP Client → MCP Server → PostgreSQL
```

**Why MCP?**
- Single point of control for all PostgreSQL operations
- Better observability — every DB operation is logged
- Agents do not need to manage connection lifecycles

**MCP Tools exposed by the server:**

| Tool | What it does |
|---|---|
| `execute_sql` | Run CREATE, DROP, INSERT, GRANT statements |
| `query_sql` | Run SELECT queries and return results |
| `get_tables` | List all tables in the database |
| `get_table_schema` | Get column definitions for a table |
| `get_row_count` | Count rows in a table |
| `get_roles` | List all roles and memberships |

---

## 12. Running the Migration

The migration requires **two terminals** — one for the MCP server and one for the pipeline.

### Terminal 1 — Start the MCP Server first

```bash
venv\Scripts\activate
cd app
python mcps/postgres_server.py
```

You should see:
```
Starting PostgreSQL MCP Server on http://127.0.0.1:8000
```

> Keep this terminal open. The MCP server must be running before starting the migration.

### Terminal 2 — Run the Migration Pipeline

```bash
venv\Scripts\activate
cd app
python main.py
```

You will see live output as each table is processed:

```
[MCP Client] Session initialized: abc123...
[Orchestrator] AI decided migration order: ['departments', 'employees']
[Schema Agent] Converting schema for 'departments'...
    [MCP Client] execute_sql: DROP TABLE IF EXISTS departments CASCADE...
[Data Agent] Migrating data for 'departments'...
[Validator] Validating 'departments'...
    [MCP Client] get_row_count: departments
--- AI Validation Report: PASS ---
```

Reports are saved to the `output/` folder after each run.

---