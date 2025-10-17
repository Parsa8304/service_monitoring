from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import app as api_app

# Create main FastAPI app
app = FastAPI(
    title="KhabarFarsi News Search API",
    description="API for searching Iranian news articles from KhabarFarsi",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the API routes
app.mount("/api", api_app)

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "KhabarFarsi API is running", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "khabarfarsi-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)