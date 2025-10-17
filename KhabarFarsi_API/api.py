from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional
from .search_khabarfarsi import create_scraper, COMMON_HEADERS, fetch_search_results, parse_results
from datetime import datetime, timezone

app = FastAPI(title="KhabarFarsi Scraper API", version="1.0.0")


class SearchBody(BaseModel):
    phrase: str = Field(..., description="Search phrase in Persian")
    limit: int = Field(50, description="Maximum number of results")


@app.post("/search")
async def search(body: SearchBody):
    if not body.phrase or not body.phrase.strip():
        raise HTTPException(status_code=400, detail="phrase is required")
    
    try:
        with create_scraper() as scraper:
            scraper.headers.update(COMMON_HEADERS)
            
            # Fetch search results directly
            html = fetch_search_results(scraper, body.phrase)
            
            # Parse results
            results = parse_results(html)
            
            # Limit results
            limited_results = results[:body.limit]
            
            # Return the actual data instead of file paths
            return {
                "query": body.phrase,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "result_count": len(limited_results),
                "results": limited_results
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")