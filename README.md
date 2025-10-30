# (Remote) YouTube MCP Server

A remote MCP (Model Context Protocol) server that provides YouTube video transcript extraction tools with OAuth authentication. It includes OAuth 2.0 authentication via Auth0, compatible with MCP clients for including ChatGPT and Claude.

Resources
- [Blog Post](https://shawhin.medium.com/how-to-build-custom-mcp-servers-for-chatgpt-1f1823f3b7b8)
- [YouTube Video]

## Quick Start

1. **Clone the repository**
```bash
git clone [<repository-url>](https://github.com/ShawhinT/yt-mcp-remote.git)
cd yt-mcp-remote
```

2. **Install dependencies** (requires Python >=3.13)
```bash
uv sync
```

3. **Configure environment variables in .env**
```bash
AUTH0_DOMAIN=your-auth0-domain
AUTH0_AUDIENCE=your-api-identifier # same as RESOURCE_SERVER_URL in this example
RESOURCE_SERVER_URL=<your-server-public-url>/mcp
```

4. **Run the server**
```bash
uv run python main.py
```

Server runs on `http://0.0.0.0:8000/mcp`

## MCP Tools

- `fetch_video_transcript(url)` - Extract and format YouTube video transcripts
- `fetch_instructions(prompt_name)` - Get writing templates (`write_blog_post`, `write_social_post`, `write_video_chapters`)

## Tech Stack

- FastMCP - MCP server framework
- Railway - Hosting remote server
- Auth0 - OAuth authentication
- youtube-transcript-api - Transcript extraction
- uv - Python dependency management
