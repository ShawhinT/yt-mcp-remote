# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YouTube MCP (Model Context Protocol) remote server that provides tools for extracting and working with YouTube video transcripts. It runs as an HTTP-accessible MCP server using FastMCP with OAuth authentication and is designed to be consumed by MCP clients remotely (including ChatGPT).

## Development Setup

This project uses **uv** for Python dependency management. The project requires Python >=3.13.

```bash
# Install dependencies
uv sync

# Run the server
uv run python main.py
```

The server runs on `0.0.0.0` using `streamable-http` transport.

## Architecture

### Core Components

**main.py** - Single-file server implementation containing:
- MCP server initialization with FastMCP
- Auth0 OAuth authentication configuration
- Server instructions loaded from `prompts/server_instructions.md`
- Two MCP tools exposed to clients

**utils/auth.py** - Auth0 token verification module:
- `Auth0TokenVerifier`: Verifies JWT tokens using Auth0's JWKS
- Validates token signature, issuer, audience, and expiration
- Caches JWKS to minimize Auth0 API calls
- Returns `AccessToken` with user info and scopes

### Authentication

The server uses OAuth 2.0 with Auth0:
- JWT tokens verified using RS256 algorithm (configurable via `AUTH0_ALGORITHMS`)
- Tokens fetched from Auth0's JWKS endpoint (`https://{domain}/.well-known/jwks.json`)
- Required environment variables (in `.env`):
  - `AUTH0_DOMAIN`: Auth0 tenant domain
  - `AUTH0_AUDIENCE`: API identifier from Auth0 dashboard
  - `RESOURCE_SERVER_URL`: Server's public URL (for OAuth flow)
  - `AUTH0_ALGORITHMS` (optional): JWT algorithm, defaults to "RS256"

The server requires the following OAuth scopes:
- `openid`
- `profile`
- `email`
- `address`
- `phone`
- `offline_access`

### Proxy Configuration

The server requires proxy credentials to fetch YouTube transcripts:
- Uses `youtube-transcript-api` with proxy support via `GenericProxyConfig`
- Required environment variables:
  - `PROXY_USERNAME`: Proxy authentication username
  - `PROXY_PASSWORD`: Proxy authentication password
  - `PROXY_URL`: Proxy server URL (format: `hostname:port`)

If proxy credentials are not configured, transcript fetching will fail with an error message.

### MCP Tools

The server exposes two tools via the MCP protocol:

1. **`fetch_video_transcript(url: str)`**
   - Extracts YouTube video transcripts using `youtube-transcript-api`
   - Formats output with timestamps: `[MM:SS] Text`
   - Extracts video ID from various YouTube URL formats using regex
   - Returns newline-separated transcript entries

2. **`fetch_instructions(prompt_name: str)`**
   - Retrieves writing instruction templates from `prompts/` directory
   - Available prompts: `write_blog_post`, `write_social_post`, `write_video_chapters`
   - Each prompt contains specific formatting guidelines and structure rules

### Prompts Directory

The `prompts/` directory contains markdown files that define:
- **server_instructions.md**: Instructions given to MCP clients about server capabilities
- **write_blog_post.md**: Blog post writing guidelines with structure (hook, intro, body sections, conclusion) and paragraph length rules (2-3 sentences max)
- **write_social_post.md**: Platform-specific social media guidelines (Twitter, LinkedIn, Instagram, Facebook) with character limits and engagement patterns
- **write_video_chapters.md**: Video chapter formatting rules requiring 20+ second chapters with timestamp and link format

These prompts define strict content structures (e.g., blog sections must be 2 paragraphs, 3 max) that clients should follow when using the transcript data.

## Server Configuration

- **Host**: `0.0.0.0` (accessible remotely)
- **Transport**: `streamable-http`

## Key Implementation Details

- Video ID extraction supports various YouTube URL formats via regex pattern: `(?:v=|\/)([0-9A-Za-z_-]{11}).*`
- Transcript timestamps are converted from seconds to `MM:SS` format for readability
- Error handling wraps YouTube API exceptions with descriptive messages
- The server uses FastMCP's decorator pattern (`@mcp.tool()`) for tool registration
- Auth0 JWT verification happens on every request via the `Auth0TokenVerifier`
