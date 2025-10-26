from fastapi import HTTPException
from pydantic import BaseModel
from services.volumetry_service import VolumetryService

volumetry_service = VolumetryService()

class StudyRequest(BaseModel):
    study_code: str
    filename: str

class VolumetryResponse(BaseModel):
    study_code: str
    status: str
    message: str
    metrics_saved: bool

async def analyze_study_handler(request: StudyRequest):
    """
    Analyze a study by study code and generate volumetry metrics.
    
    Args:
        request: StudyRequest containing the study_code
        
    Returns:
        VolumetryResponse with analysis results
    """
    try:
        # Process the study
        result = volumetry_service.process_study(request.study_code, request.filename)
        
        return VolumetryResponse(
            study_code=request.study_code,
            status="success",
            message=f"Study {request.study_code} processed successfully",
            metrics_saved=result["metrics_saved"]
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")