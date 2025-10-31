import re
import os

from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from pydantic import AnyHttpUrl
from dotenv import load_dotenv

from utils.auth import create_auth0_verifier

# Load environment variables from .env file
load_dotenv()

# Get Auth0 configuration from environment
auth0_domain = os.getenv("AUTH0_DOMAIN")
resource_server_url = os.getenv("RESOURCE_SERVER_URL")

if not auth0_domain:
    raise ValueError("AUTH0_DOMAIN environment variable is required")
if not resource_server_url:
    raise ValueError("RESOURCE_SERVER_URL environment variable is required")

# Load server instructions
with open("prompts/server_instructions.md", "r") as file:
    server_instructions = file.read()

# Initialize Auth0 token verifier
token_verifier = create_auth0_verifier()

# Create an MCP server with OAuth authentication
mcp = FastMCP(
    "yt-mcp",
    instructions=server_instructions,
    host="0.0.0.0",
    # OAuth Configuration
    token_verifier=token_verifier,
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(f"https://{auth0_domain}/"),
        resource_server_url=AnyHttpUrl(resource_server_url),
        required_scopes=["openid", "profile", "email", "address", "phone"],
    ),
)

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

    def format_transcript(transcript):
        """Format transcript entries with timestamps"""
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

    try:
        # Get proxy credentials from environment
        proxy_username = os.getenv("PROXY_USERNAME")
        proxy_password = os.getenv("PROXY_PASSWORD")
        proxy_url_base = os.getenv("PROXY_URL")

        if not proxy_username or not proxy_password or not proxy_url_base:
            raise ValueError("Proxy credentials not configured. Set PROXY_USERNAME, PROXY_PASSWORD, and PROXY_URL environment variables.")

        # Construct proxy URLs with credentials
        http_proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_url_base}"
        https_proxy_url = f"https://{proxy_username}:{proxy_password}@{proxy_url_base}"

        proxy_config = GenericProxyConfig(
            http_url=http_proxy_url,
            https_url=https_proxy_url
        )

        ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
        transcript = ytt_api.fetch(video_id)
        return format_transcript(transcript)

    except Exception as e:
        raise Exception(f"Error fetching transcript with proxy: {str(e)}")

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