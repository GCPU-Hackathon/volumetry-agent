from fastapi import FastAPI
from controllers.volumetry_controller import analyze_study_handler, get_study_metrics_handler, StudyRequest, VolumetryResponse
import uvicorn
import os

app = FastAPI(
    title="Volumetry Agent API",
    description="API for medical image volumetry analysis",
    version="1.0.0"
)

@app.post("/analyze", response_model=VolumetryResponse)
async def analyze_study(request: StudyRequest):
    """
    Analyze a study by study code and generate volumetry metrics.
    """
    return await analyze_study_handler(request)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )