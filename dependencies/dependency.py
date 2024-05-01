from fastapi import Depends,HTTPException,status
from fastapi.security import APIKeyHeader
from config.settings import Settings


api_key_header = APIKeyHeader(name="Summarize-API-Key")
setting = Settings()


async def check_api_key(api_key: str = Depends(api_key_header)):
    if api_key != setting.SUMMARIZE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key"
        )