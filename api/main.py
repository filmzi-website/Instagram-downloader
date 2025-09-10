from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
from utils.ytdlp_helper import extract_info

app = FastAPI(title="Instagram Downloader API")

@app.get("/api/info")
async def info(url: str = Query(..., description="Instagram URL (post/reel/story/profile)")):
    """Return parsed media info and available formats (json)"""
    try:
        info = await extract_info(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return JSONResponse(content=info)

@app.get("/api/download")
async def download(url: str = Query(..., description="Instagram URL"), format_id: Optional[str] = None):
    """
    Return a 302 redirect to a direct media URL.
    If format_id is provided, try to match that format; otherwise return best available direct URL.
    """
    try:
        info = await extract_info(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    formats = info.get("formats") or []
    if not formats:
        # maybe this is an image-only post
        image = info.get("thumbnail") or info.get("display_url")
        if image:
            return RedirectResponse(url=image)
        raise HTTPException(status_code=404, detail="No downloadable media found")

    # choose a format
    fmt = None
    if format_id:
        for f in formats:
            if str(f.get("format_id")) == str(format_id) or f.get("ext") == format_id:
                fmt = f
                break
    if not fmt:
        # pick best (highest resolution + direct URL)
        # prefer 'url' in format
        formats_with_url = [f for f in formats if f.get("url")]
        if not formats_with_url:
            raise HTTPException(status_code=404, detail="No downloadable formats with direct url")
        fmt = sorted(formats_with_url, key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)[0]

    direct = fmt.get("url")
    if not direct:
        raise HTTPException(status_code=404, detail="Chosen format has no direct url")

    return RedirectResponse(url=direct)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
