# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YouTube MCP (Model Context Protocol) remote server that provides tools for extracting and working with YouTube video transcripts. It runs as an HTTP-accessible MCP server using FastMCP and is designed to be consumed by MCP clients remotely.

## Development Setup

This project uses **uv** for Python dependency management. The project requires Python >=3.13.

```bash
# Install dependencies
uv sync

# Run the server
uv run python main.py
```

The server runs on `0.0.0.0:8000` using `streamable-http` transport for remote access.

## Architecture

### Core Components

**main.py** - Single-file server implementation containing:
- MCP server initialization with FastMCP
- Server instructions loaded from `prompts/server_instructions.md`
- Two MCP tools exposed to clients

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
- **Port**: `8000`
- **Transport**: `streamable-http`
- **Logging**: MCP INFO logs suppressed to WARNING level to reduce console noise

## Key Implementation Details

- Video ID extraction supports various YouTube URL formats via regex pattern: `(?:v=|\/)([0-9A-Za-z_-]{11}).*`
- Transcript timestamps are converted from seconds to `MM:SS` format for readability
- Error handling wraps YouTube API exceptions with descriptive messages
- The server uses FastMCP's decorator pattern (`@mcp.tool()`) for tool registration
