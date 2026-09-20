from fastapi import APIRouter, File, UploadFile

from src.schemas.targeting_report import KeywordPerformance
from src.services import targeting_report_service

router = APIRouter()


@router.post("/targeting-report", response_model=list[KeywordPerformance])
async def upload_targeting_report(file: UploadFile = File(...)) -> list[KeywordPerformance]:
    content = await file.read()
    return targeting_report_service.ingest(content)
