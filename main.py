import json
import subprocess
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Any

# Define a Pydantic model for the response from /api/info
class MediaInfo(BaseModel):
    title: Optional[str] = Field(None, description="Title of the media.")
    uploader: Optional[str] = Field(None, description="Uploader of the media.")
    url: str = Field(..., description="Direct URL of the best available media format.")
    thumbnail: Optional[str] = Field(None, description="URL of the media thumbnail.")
    formats: Optional[List[dict]] = Field(None, description="List of all available formats with their details.")

# Define a Pydantic model for the health check response
class HealthStatus(BaseModel):
    status: str = "ok"

app = FastAPI(
    title="Instagram Downloader API",
    description="A simple API to download Instagram media using yt-dlp, deployed on Vercel.",
    version="1.0.0"
)

def run_ytdlp(command: list) -> str:
    """
    Helper function to run the yt-dlp command in a subprocess and capture output.
    Raises an HTTPException on failure.
    """
    try:
        # We need to run yt-dlp with the --no-warnings flag to suppress
        # warnings that can interfere with JSON output.
        process = subprocess.run(
            ["yt-dlp", "--no-warnings"] + command,
            capture_output=True,
            text=True,
            check=True
        )
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip()
        print(f"yt-dlp error: {error_message}")
        if "unable to download video" in error_message.lower() or "this video is unavailable" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media not found or is private: {error_message}"
            )
        elif "unsupported url" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid URL: {error_message}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {error_message}"
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="yt-dlp not found. Please ensure it is installed and available in the system PATH."
        )

@app.get(
    "/api/info",
    response_model=MediaInfo,
    summary="Get media info and available formats",
    description="Returns JSON with detailed media information, including a list of available formats, from a given Instagram URL (post, reel, story, or profile picture)."
)
async def get_media_info(url: str):
    """
    Endpoint to retrieve detailed media information.
    """
    command = ["--dump-single-json", "--ignore-config", url]
    
    # Run yt-dlp to get the full JSON info
    json_output = run_ytdlp(command)
    data = json.loads(json_output)

    # Clean up the formats list to be more readable
    formats_list = []
    if "formats" in data:
        for fmt in data["formats"]:
            formats_list.append({
                "format_id": fmt.get("format_id"),
                "ext": fmt.get("ext"),
                "resolution": fmt.get("resolution"),
                "vcodec": fmt.get("vcodec"),
                "acodec": fmt.get("acodec"),
                "file_size": fmt.get("filesize_approx"),
                "url": fmt.get("url")
            })

    # Find the best format URL for the main URL field
    best_format_url = data.get("url")

    media_info = {
        "title": data.get("title", "No Title"),
        "uploader": data.get("uploader", "Unknown Uploader"),
        "url": best_format_url,
        "thumbnail": data.get("thumbnail"),
        "formats": formats_list
    }

    return MediaInfo(**media_info)

@app.get(
    "/api/download",
    summary="Download media (redirect)",
    description="Redirects (302) to the direct URL of the Instagram media. You can specify a format ID to get a specific quality, or leave it blank to get the best available. This does not download the file to the server."
)
async def download_media(url: str, format_id: Optional[str] = None):
    """
    Endpoint to get a direct download URL.
    """
    command = ["-g", "--ignore-config"]
    if format_id:
        command += ["-f", format_id]
    
    command.append(url)
    
    # Run yt-dlp to get the direct URL
    download_url = run_ytdlp(command)
    
    if not download_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find a download URL for the specified media and format."
        )
        
    return RedirectResponse(download_url, status_code=status.HTTP_302_FOUND)

@app.get(
    "/api/health",
    response_model=HealthStatus,
    summary="Health check",
    description="Returns a simple status to indicate the API is running."
)
async def health_check():
    """
    Endpoint for a simple health check.
    """
    return {"status": "ok"}
