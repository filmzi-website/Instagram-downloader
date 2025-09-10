import asyncio
from yt_dlp import YoutubeDL

YTDL_OPTS = {
    'skip_download': True,
    'quiet': True,
    'no_warnings': True
}

async def extract_info(url: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_sync, url)

def _extract_sync(url: str) -> dict:
    with YoutubeDL(YTDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
        keys_keep = ['id','title','uploader','thumbnail','display_id','formats','duration','view_count','like_count']
        return {k: info.get(k) for k in keys_keep if k in info}
