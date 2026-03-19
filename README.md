# DuckDuckGo MCP Server

A lightweight [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI agents the ability to search the web via DuckDuckGo and fetch content from any URL — no API key required.

## Features

- **Web search** — query DuckDuckGo and receive ranked results with titles, URLs, and snippets
- **Page fetching** — retrieve and parse the readable text content of any webpage
- **LLM-powered relevance extraction** — `fetch_content` routes raw page text through a local/remote LLM and returns only the passages relevant to the query
- **Rate limiting** — built-in sliding-window rate limiter protects against throttling
- **Stateless HTTP transport** — compatible with any MCP client that speaks Streamable HTTP
- **Health endpoint** — `/actuator/health` for container orchestration probes
- **Docker-ready** — minimal Alpine-based image included

## Tools

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `search` | Search DuckDuckGo and return the top N results | `query: string` | Ranked list of results (title, URL, snippet) |
| `fetch_content` | Fetch a webpage and return only the content relevant to the query | `url: string`, `query: string` | Passages from the page relevant to the query, extracted by an LLM |

### `search`

Queries the DuckDuckGo HTML endpoint (no JavaScript required), parses the results, and returns them in a structured natural-language format suited for LLM consumption. Ad results are automatically filtered out.

```
Found 5 search results:

1. Example Title
   URL: https://example.com
   Summary: A short snippet describing the page content.
...
```

### `fetch_content`

Fetches a URL with `httpx`, strips navigation, headers, footers, scripts, and style elements, then passes the cleaned text together with the original `query` to a local/remote LLM (`ContentExtractor`). The LLM returns **only the passages that are directly relevant to the query**, preserving the original wording without summarising or paraphrasing. If no relevant content is found, the tool returns `"The fetched page does not contain content relevant to the query."`

The LLM endpoint must be OpenAI-compatible and is configured via the `LLM_BASE_URL` and `LLM_MODEL` environment variables (see [Configuration](#configuration)).

## Requirements

- Python >= 3.10

## Installation

### From source

```bash
git clone https://github.com/your-org/duckduckgo-mcp-server.git
cd duckduckgo-mcp-server

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate

pip install -e .
```

## Configuration

Copy the example environment file and adjust as needed:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Port the HTTP server listens on |
| `MAX_RESULTS` | `5` | Maximum number of search results returned per query |
| `LLM_BASE_URL` | *(required)* | Base URL of the OpenAI-compatible LLM endpoint used by `fetch_content` |
| `LLM_MODEL` | `qwen3.5:0.8b` | Model name passed to the LLM endpoint |

## Running the Server

```bash
python server.py
```

The server starts on `http://0.0.0.0:<PORT>` and exposes:

| Path | Description |
|------|-------------|
| `/mcp` | MCP Streamable HTTP endpoint |
| `/actuator/health` | Health check — returns `{"status": "ok"}` |

## Docker

### Build

```bash
docker build -t duckduckgo-mcp-server .
```

### Run

```bash
docker run -p 8080:8080 duckduckgo-mcp-server
```

### Run with custom configuration

```bash
docker run -p 9000:9000 \
  -e PORT=9000 \
  -e MAX_RESULTS=10 \
  duckduckgo-mcp-server
```

## Connecting an MCP Client

Configure your MCP client to connect to the server's Streamable HTTP endpoint. Below are examples for common clients.

### Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "duckduckgo": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

### Generic HTTP client configuration

```
Transport: Streamable HTTP
URL:       http://localhost:8080/mcp
```

## Rate Limiting

Both tools enforce an in-process sliding-window rate limiter to avoid triggering DuckDuckGo's bot-detection or overwhelming remote servers:

| Component | Limit |
|-----------|-------|
| `DuckDuckGoSearcher` | 30 requests / minute |
| `WebContentFetcher` | 20 requests / minute |

When the limit is reached the request waits automatically — no error is raised.

## Acknowledgements

The search parsing and webpage fetching logic is inspired by [nickclyde/duckduckgo-mcp-server](https://github.com/nickclyde/duckduckgo-mcp-server).