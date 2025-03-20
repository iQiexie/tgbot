import json
import re
import time
import traceback
import uuid
from json import JSONDecodeError
from typing import Any, Dict

import structlog
from fastapi import FastAPI
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.patches import WebappData
from app.patches import bot
from app.utils import struct_log

logger = structlog.stdlib.get_logger()


LOGGING_SENSITIVE_FIELDS = (
    "password",
    "token",
    "Authorization",
    "Authentication",
    "authorization",
    "authentication",
    "x-api-key",
    "x-cmc_pro_api_key",
)

LOGGING_SENSITIVE_REPLACEMENT = "******"

LOGGING_DISABLED_ENDPOINTS = ("/metrics",)


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        BaseHTTPMiddleware.__init__(self, app=app, dispatch=self.dispatch)
        regex_str = r'("[^"]*?(?={keywords})[^"]*":\s*")[^"]*"'
        regex_with_keys = regex_str.format(keywords="|".join(LOGGING_SENSITIVE_FIELDS))
        self.regex_pattern = re.compile(regex_with_keys)
        self.substitution = rf'\1{LOGGING_SENSITIVE_REPLACEMENT}"'

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.time()
        request_dict = await self._get_request_dict(request=request)

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(**request_dict)

        try:
            exception = None
            response = await call_next(request)
            response.headers["X-Error-Trace"] = request_dict["key"]
        except Exception as ex:
            exception = ex
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Server Error. Please try again later"},
            )
            response.headers["X-Error-Trace"] = request_dict["key"]

        total_time = time.time() - start
        duration = f"{total_time:.3f}"
        event = f"{response.status_code} | {duration} s"

        if (exception is None) and (request.url.path not in LOGGING_DISABLED_ENDPOINTS):
            logger.info(event=event, status_code=response.status_code, duration=duration)

        if exception:
            formatted_exception = traceback.format_exception(exception)

            logger.error(
                event="A server error has occurred",
                exception=formatted_exception,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                duration=duration,
            )

        traceback.print_exception(exception)
        return response

    @staticmethod
    def decode_auth_token(request: Request) -> WebappData | None:
        auth_token = request.headers.get("token", "")
        if not auth_token:
            return

        try:
            return bot.auth_webapp(webapp_data=auth_token)
        except Exception:  # noqa
            return None

    async def _get_request_dict(self, request: Request) -> Dict[str, Any]:
        auth_data = self.decode_auth_token(request=request)
        content_type = request.headers.get("Content-Type", "")
        client_ip = request.headers.get("cf-connecting-ip") or request.headers.get("x-real-ip") or request.client.host
        body = ""

        if content_type.startswith("application/json"):
            body = await request.body()

            try:
                body = json.dumps(json.loads(body), ensure_ascii=False)
                body = self._protect_body(body=body)
            except JSONDecodeError:
                pass

        url = str(request.url)
        query = json.dumps(dict(request.query_params.items()), ensure_ascii=False)  # noqa
        method = str(request.method)
        key = str(uuid.uuid4())

        return {
            "method": method,
            "url": url,
            "query": query,
            "body": body,
            "client_ip": client_ip,
            "user_id": auth_data.telegram_id if auth_data else None,
            "key": key,
        }

    def _protect_body(self, body: str) -> str:
        try:
            return re.sub(
                self.regex_pattern,
                repl=self.substitution,
                string=body,
            )
        except Exception as e:
            struct_log(event="Failed to protect string", exception=traceback.format_exception(e))
            return body
