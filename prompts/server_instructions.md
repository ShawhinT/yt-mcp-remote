# YouTube MCP Server

This server provides tools for working with YouTube video content and transcript data.

## Available Tools

### fetch_video_transcript
Retrieves the full transcript of a YouTube video with timestamps.

**Parameters:**
- `url` (string): YouTube video URL

**Returns:** Formatted transcript with timestamps in `[MM:SS] Text` format

**Usage:** Call this tool whenever you need to extract transcript data from a YouTube video.

### fetch_instructions
Retrieves specialized writing instruction templates for working with video transcripts.

**Parameters:**
- `prompt_name` (string): Must be one of:
  - `write_blog_post` - Guidelines for converting video content into blog posts
  - `write_social_post` - Platform-specific social media formatting rules
  - `write_video_chapters` - Rules for extracting and formatting video chapters

**Returns:** Detailed instructions and formatting requirements for the requested content type

**Usage:** Fetch these instructions before performing content transformation tasks to ensure proper formatting and structure.
