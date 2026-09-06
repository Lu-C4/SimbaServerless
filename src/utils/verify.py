import hmac
import logging
import os
import time

from dotenv import load_dotenv
from fastapi import Request, Response
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from starlette.middleware.base import BaseHTTPMiddleware

load_dotenv()

CLIENT_PUBLIC_KEY = os.environ.get("CLIENT_PUBLIC_KEY")
ENCRYPT_KEY = os.environ.get("ENCRYPT_KEY")
SIGNATURE_MAX_AGE_SECONDS = 300
logger = logging.getLogger(__name__)


def is_fresh_timestamp(timestamp: str, now: float | None = None) -> bool:
    try:
        return abs((time.time() if now is None else now) - int(timestamp)) <= SIGNATURE_MAX_AGE_SECONDS
    except (TypeError, ValueError):
        return False

def verify_key(
    raw_body: bytes, signature: str, timestamp: str, client_public_key: str
) -> bool:
    message = timestamp.encode() + raw_body
    try:
        vk = VerifyKey(bytes.fromhex(client_public_key))
        vk.verify(message, bytes.fromhex(signature))
        return True
    except (BadSignatureError, TypeError, ValueError):
        return False


async def set_body(request: Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body}

    request._receive = receive


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path == "/recruit":
            provided_key = request.headers.get("ENCRYPT_KEY")
            if not provided_key or not ENCRYPT_KEY or not hmac.compare_digest(provided_key, ENCRYPT_KEY):
                return Response("Bad request signature", status_code=401)
            return await call_next(request)

        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")
        request_body = await get_body(request)

        if (
            not signature
            or not timestamp
            or not CLIENT_PUBLIC_KEY
            or not is_fresh_timestamp(timestamp)
            or not verify_key(request_body, signature, timestamp, CLIENT_PUBLIC_KEY)
        ):
            return Response("Bad request signature", status_code=401)
        return await call_next(request)
