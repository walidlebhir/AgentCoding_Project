from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.security.jwt_handler import decode_access_token
from src.Services.user_service import get_user_by_id
from src.Config.database import SessionLocal

PUBLIC_PATHS = {"/", "/docs", "/openapi.json", "/redoc", "/health", "/login", "/register"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if any(path.startswith(p) for p in PUBLIC_PATHS) or path.startswith("/admin/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authorization header"},
            )

        token = auth_header.removeprefix("Bearer ")
        payload = decode_access_token(token)
        if payload is None:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
            )

        db = SessionLocal()
        try:
            user = get_user_by_id(db, payload["sub"])
            if user is None:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found"},
                )
            request.state.user = user
        finally:
            db.close()

        return await call_next(request)
