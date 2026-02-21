# mcp-gemini-chat-cli

A command-line chat application powered by **Google Gemini** and the **Model Context Protocol (MCP)**. It lets you converse with Gemini while giving the model access to documents and tools through an MCP server, all from your terminal.

## Features

- **Interactive CLI chat** with Google Gemini (default model: `gemini-2.5-flash`)
- **Document retrieval** — mention documents with `@` to inject their content into the conversation
- **MCP tool use** — Gemini can autonomously call tools (read, edit documents) exposed by the MCP server
- **Prompt commands** — use `/format` or `/summarize` to trigger predefined prompt workflows
- **Tab completion** for commands and document references
- **Extensible** — plug in additional MCP servers by passing their scripts as arguments

## Prerequisites

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/apikey)

## Setup

### 1. Configure environment variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY="your-api-key-here"
GEMINI_MODEL="gemini-2.5-flash"   # optional, defaults to gemini-2.5-flash
```

### 2. Install & run

#### Option A — with [uv](https://github.com/astral-sh/uv) (recommended)

```bash
pip install uv          # install uv if you don't have it
uv venv && source .venv/bin/activate
uv pip install -e .
uv run main.py
```

#### Option B — plain pip

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
python main.py
```

> **Windows:** replace `source .venv/bin/activate` with `.venv\Scripts\activate`.

### 3. (Optional) Connect additional MCP servers

Pass extra server scripts as arguments:

```bash
python main.py path/to/another_mcp_server.py
```

## Usage

| Action | Syntax | Example |
|---|---|---|
| Chat | Just type your message | `What is a condenser tower?` |
| Mention a document | `@<doc_id>` | `Tell me about @report.pdf` |
| Run a prompt command | `/<command> <doc_id>` | `/summarize deposition.md` |

Press **Tab** to auto-complete commands and document IDs.

### Available prompt commands

| Command | Description |
|---|---|
| `/format` | Rewrites a document in Markdown format |
| `/summarize` | Produces a concise summary of a document |

## Project Structure

```
├── main.py            # Entry point — wires up Gemini, MCP client & CLI
├── mcp_server.py      # MCP server exposing documents, tools & prompts
├── mcp_client.py      # MCP client wrapper (stdio transport)
├── core/
│   ├── gemini.py      # Gemini API service class
│   ├── chat.py        # Base chat loop with tool-calling support
│   ├── cli_chat.py    # CLI-specific chat (documents, commands, resources)
│   ├── cli.py         # Terminal UI (prompt-toolkit)
│   └── tools.py       # Tool manager — bridges MCP tools ↔ Gemini functions
├── pyproject.toml
└── README.md
```

## How It Works

1. **main.py** starts the MCP document server (`mcp_server.py`) as a subprocess over stdio and initialises a Gemini client.
2. The CLI presents an interactive prompt. User input is processed by `CliChat`:
   - `@mentions` are resolved via MCP resources and injected as context.
   - `/commands` fetch predefined MCP prompts and add them to the conversation.
   - Plain messages are sent directly to Gemini.
3. Gemini receives the conversation along with MCP tool declarations. If the model decides to call a tool (e.g. `read_doc_contens`, `edit_doc`), the tool call is forwarded to the appropriate MCP client and the result is fed back to Gemini.
4. The loop continues until Gemini returns a final text response, which is printed to the terminal.
