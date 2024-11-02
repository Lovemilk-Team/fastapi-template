from fastapi import Request, FastAPI

from ..structs.responses import BaseResponse


def add_response_middleware(app: FastAPI):
    async def _response_middleware(request: Request, call_next):
        response = await call_next(request)
        if isinstance(response, BaseResponse):
            return response.to_response()

        return response

    app.middleware('http')(_response_middleware)
