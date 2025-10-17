import httpx
from fastapi import FastAPI, HTTPException, Form
from prometheus_fastapi_instrumentator import Instrumentator
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Twitter API Proxy",
    description="API for fetching Twitter posts data",
    version="1.0.0"
)


instr = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
)

instr.instrument(app).expose(app, endpoint="/metrics")
# Twitter API endpoint configuration
TWITTER_API_BASE = "http://82.115.24.30:8080/tw.php"

@app.get("/")
async def root():
    return {"message": "Twitter API Proxy is running", "status": "active"}

@app.post("/search/twitter")
async def search_twitter_posts(
    keywords: List[str] = Form(..., description="Keywords to search for"),
    post_type: str = Form(default="Top", description="Type of posts: 'Top' or 'Latest'")
) -> Dict:
    """
    Search for Twitter posts using keywords.
    
    Args:
        keywords: List of keywords to search for
        post_type: Type of posts to fetch - 'Top' or 'Latest'
    
    Returns:
        Dictionary containing Twitter posts data
    """
    try:
        logger.info(f"Searching Twitter posts for keywords: {keywords}, type: {post_type}")
        
        # Validate post_type
        if post_type not in ["Top", "Latest"]:
            raise HTTPException(
                status_code=400, 
                detail="post_type must be either 'Top' or 'Latest'"
            )
        
        if not keywords:
            raise HTTPException(
                status_code=400,
                detail="At least one keyword is required"
            )
        
        # Prepare all form data as files to match the exact curl format
        files = []
        # Add type parameter
        files.append(("type", (None, post_type)))
        # Add keywords as key[] parameters
        for keyword in keywords:
            files.append(("key[]", (None, keyword)))
        
        # Make request to Twitter API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                TWITTER_API_BASE,
                files=files
            )
            
            logger.info(f"Twitter API response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    # Try to parse as JSON
                    result = response.json()
                    
                    # Add metadata
                    return {
                        "success": True,
                        "keywords": keywords,
                        "post_type": post_type,
                        "data": result,
                        "total_posts": len(result) if isinstance(result, list) else 1,
                        "meta": {
                            "api_endpoint": TWITTER_API_BASE,
                            "response_type": "json"
                        }
                    }
                except Exception as json_error:
                    # If not JSON, return as text
                    logger.warning(f"Response not JSON, returning as text: {json_error}")
                    return {
                        "success": True,
                        "keywords": keywords,
                        "post_type": post_type,
                        "data": response.text,
                        "meta": {
                            "api_endpoint": TWITTER_API_BASE,
                            "response_type": "text"
                        }
                    }
            else:
                logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Twitter API returned error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to Twitter API: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to Twitter API: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/search/twitter")
async def search_twitter_get(
    keywords: str,
    post_type: str = "Top"
) -> Dict:
    """
    GET endpoint for Twitter search (alternative to POST).
    
    Args:
        keywords: Comma-separated keywords to search for
        post_type: Type of posts to fetch - 'Top' or 'Latest'
    """
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    return await search_twitter_posts(keywords=keyword_list, post_type=post_type)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test connection to external API
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(TWITTER_API_BASE.replace('tw.php', ''))
            
        return {
            "status": "healthy",
            "twitter_api_accessible": response.status_code < 500,
            "service": "twitter_api_proxy"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "twitter_api_accessible": False,
            "error": str(e),
            "service": "twitter_api_proxy"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)