from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
from utils.ytdlp_helper import extract_info

app = FastAPI(title="Instagram Downloader API")

@app.get("/api/info")
async def info(url: str = Query(..., description="Instagram URL (post/reel/story/profile)")):
    """Return parsed media info and available formats (JSON)"""
    try:
        info_data = await extract_info(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting info: {str(e)}")
    return JSONResponse(content=info_data)

@app.get("/api/download")
async def download(url: str = Query(..., description="Instagram URL"), format_id: Optional[str] = None):
    """Return a 302 redirect to a direct media URL."""
    try:
        info_data = await extract_info(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting info: {str(e)}")

    formats = info_data.get("formats") or []
    if not formats:
        image_url = info_data.get("thumbnail") or info_data.get("display_url")
        if image_url:
            return RedirectResponse(url=image_url)
        raise HTTPException(status_code=404, detail="No downloadable media found")

    chosen_format = None
    if format_id:
        for f in formats:
            if str(f.get("format_id")) == str(format_id) or f.get("ext") == format_id:
                chosen_format = f
                break
    if not chosen_format:
        formats_with_url = [f for f in formats if f.get("url")]
        if not formats_with_url:
            raise HTTPException(status_code=404, detail="No downloadable formats with direct URL")
        chosen_format = sorted(formats_with_url, key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)[0]

    direct_url = chosen_format.get("url")
    if not direct_url:
        raise HTTPException(status_code=404, detail="Chosen format has no direct URL")

    return RedirectResponse(url=direct_url)

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Instagram Downloader API is running"}
