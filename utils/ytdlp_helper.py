import asyncio
from yt_dlp import YoutubeDL

YTDL_OPTS = {
    'skip_download': True,
    'quiet': True,
    'no_warnings': True,
    # avoid console progress output
}

async def extract_info(url: str) -> dict:
    """Run yt-dlp extract_info in a thread to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_sync, url)

def _extract_sync(url: str) -> dict:
    with YoutubeDL(YTDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
        # sanitize: remove large/unnecessary fields
        keys_keep = ['id','title','uploader','thumbnail','display_id','formats','duration','view_count','like_count']
        return {k: info.get(k) for k in keys_keep if k in info}
