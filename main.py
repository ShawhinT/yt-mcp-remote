from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from youtube_transcript_api import YouTubeTranscriptApi
from pydantic import AnyHttpUrl
from dotenv import load_dotenv
import re
import os

# Load environment variables from .env file
load_dotenv()

# Suppress MCP INFO logs to reduce console output
import logging
logging.getLogger("mcp").setLevel(logging.WARNING)

# Import Auth0 token verifier
from utils.auth import create_auth0_verifier

# Load server instructions
with open("prompts/server_instructions.md", "r") as file:
    server_instructions = file.read()

# Initialize Auth0 token verifier
token_verifier = create_auth0_verifier()

# Get Auth0 configuration from environment
auth0_domain = os.getenv("AUTH0_DOMAIN")
resource_server_url = os.getenv("RESOURCE_SERVER_URL", "http://localhost:8000")

# Create an MCP server with OAuth authentication
mcp = FastMCP(
    "yt-mcp",
    instructions=server_instructions,
    host="0.0.0.0",
    port=8000,
    token_verifier=token_verifier,
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(f"https://{auth0_domain}/"),
        resource_server_url=AnyHttpUrl(resource_server_url),
        required_scopes=[],  # Temporarily disabled for testing
    ),
)

# ChatGPT-required tools (minimal stubs for testing)
@mcp.tool()
def search(query: str) -> dict:
    """
    Search for content (stub for ChatGPT compatibility testing)

    Args:
        query (str): Search query

    Returns:
        dict: Search results with id, title, url
    """
    return {
        "results": [{
            "id": "test-123",
            "title": "Test Video Result",
            "url": "https://youtube.com/watch?v=test-123"
        }]
    }

@mcp.tool()
def fetch(id: str) -> dict:
    """
    Fetch content by ID (stub for ChatGPT compatibility testing)

    Args:
        id (str): Content ID

    Returns:
        dict: Content with id, title, text, url, metadata
    """
    return {
        "id": id,
        "title": f"Test Document {id}",
        "text": "This is test content for troubleshooting ChatGPT connection.",
        "url": f"https://example.com/{id}",
        "metadata": {"source": "test"}
    }

# Original tools (keeping for backwards compatibility)
@mcp.tool()
def fetch_video_transcript(url: str) -> str:
    """
    Extract transcript with timestamps from a YouTube video URL and format it for LLM consumption
    
    Args:
        url (str): YouTube video URL
        
    Returns:
        str: Formatted transcript with timestamps, where each entry is on a new line
             in the format: "[MM:SS] Text"
    """
    # Extract video ID from URL
    video_id_pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    video_id_match = re.search(video_id_pattern, url)
    
    if not video_id_match:
        raise ValueError("Invalid YouTube URL")
    
    video_id = video_id_match.group(1)
    
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        
        # Format each entry with timestamp and text
        formatted_entries = []
        for entry in transcript:
            # Convert seconds to MM:SS format
            minutes = int(entry.start // 60)
            seconds = int(entry.start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            
            formatted_entry = f"{timestamp} {entry.text}"
            formatted_entries.append(formatted_entry)
        
        # Join all entries with newlines
        return "\n".join(formatted_entries)
    
    except Exception as e:
        raise Exception(f"Error fetching transcript: {str(e)}")

@mcp.tool()
def fetch_instructions(prompt_name: str) -> str:
    """
    Fetch instructions for a given prompt name from the prompts/ directory

    Args:
        prompt_name (str): Name of the prompt to fetch instructions for
        Available prompts: 
            - write_blog_post
            - write_social_post
            - write_video_chapters

    Returns:
        str: Instructions for the given prompt
    """
    script_dir = os.path.dirname(__file__)
    prompt_path = os.path.join(script_dir, "prompts", f"{prompt_name}.md")
    with open(prompt_path, "r") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run(transport='streamable-http')