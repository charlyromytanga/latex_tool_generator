import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def require_api_key(api_key: str = Security(_key_header)) -> str:
    expected = os.getenv("API_GATEWAY_KEY", "")
    if not expected or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou absente",
        )
    return api_key
