import os
import socket
import ssl
from json import dumps, loads
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

import httpx
from dotenv import load_dotenv

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b"
OPENROUTER_TIMEOUT_SECONDS = 15.0
# Uses the domain name so SSL verification works correctly (verify=True default).
# Trade-off: if DNS is completely broken, this fallback also fails — acceptable for MVP.
DOH_RESOLVER_URL = "https://cloudflare-dns.com/dns-query"

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class OpenRouterError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def get_openrouter_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise OpenRouterError("OPENROUTER_API_KEY environment variable is required", status_code=500)
    return key


def run_openrouter_prompt(prompt: str, max_tokens: int = 32) -> dict[str, Any]:
    key = get_openrouter_api_key()

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(OPENROUTER_URL, json=payload, headers=headers, timeout=OPENROUTER_TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise OpenRouterError("OpenRouter request failed") from exc
    except httpx.HTTPError as exc:
        response = _post_with_doh_fallback(
            url=OPENROUTER_URL,
            payload=payload,
            headers=headers,
            original_error=exc,
        )

    data = response.json()
    choices = data.get("choices")
    if not choices or not isinstance(choices, list) or not choices[0].get("message"):
        raise OpenRouterError("Unexpected OpenRouter response shape")

    text = choices[0]["message"].get("content")
    if not isinstance(text, str) or not text.strip():
        raise OpenRouterError("Unexpected OpenRouter response shape")

    return {
        "prompt": prompt,
        "response_text": text,
    }


def _post_with_doh_fallback(
    *,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    original_error: Exception,
) -> httpx.Response:
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    if not hostname:
        raise OpenRouterError("OpenRouter request failed") from original_error

    try:
        address = _resolve_with_doh(hostname)
        return _post_json_via_ip(
            host=hostname,
            address=address,
            path=parsed_url.path,
            payload=payload,
            headers=headers,
        )
    except Exception as exc:
        raise OpenRouterError("OpenRouter request failed") from exc


def _resolve_with_doh(hostname: str) -> str:
    response = httpx.get(
        f"{DOH_RESOLVER_URL}?name={hostname}&type=A",
        headers={"accept": "application/dns-json"},
        timeout=OPENROUTER_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    data = response.json()
    answers = data.get("Answer", [])
    for answer in answers:
        if answer.get("type") == 1 and isinstance(answer.get("data"), str):
            return answer["data"]

    raise OpenRouterError("OpenRouter request failed")


def _post_json_via_ip(
    *,
    host: str,
    address: str,
    path: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> httpx.Response:
    body = dumps(payload).encode("utf-8")
    request_headers = {
        "Host": host,
        "Content-Type": "application/json",
        "Authorization": headers["Authorization"],
        "Content-Length": str(len(body)),
        "Accept": "application/json",
        "Accept-Encoding": "identity",
        "Connection": "close",
    }
    request_lines = [f"POST {path} HTTP/1.1"]
    request_lines.extend(f"{key}: {value}" for key, value in request_headers.items())
    request_message = ("\r\n".join(request_lines) + "\r\n\r\n").encode("ascii") + body

    context = ssl.create_default_context()
    with socket.create_connection((address, 443), timeout=OPENROUTER_TIMEOUT_SECONDS) as tcp_socket:
        with context.wrap_socket(tcp_socket, server_hostname=host) as tls_socket:
            tls_socket.sendall(request_message)
            raw_response = bytearray()
            while True:
                chunk = tls_socket.recv(4096)
                if not chunk:
                    break
                raw_response.extend(chunk)

    return _build_httpx_response(bytes(raw_response), host)


def _build_httpx_response(raw_response: bytes, host: str) -> httpx.Response:
    try:
        header_bytes, body = raw_response.split(b"\r\n\r\n", 1)
    except ValueError as exc:
        raise OpenRouterError("OpenRouter request failed") from exc

    header_lines = header_bytes.decode("iso-8859-1").split("\r\n")
    status_line = header_lines[0]
    try:
        _, status_code_text, _ = status_line.split(" ", 2)
    except ValueError as exc:
        raise OpenRouterError("OpenRouter request failed") from exc

    headers = {}
    for line in header_lines[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()

    if headers.get("Transfer-Encoding", "").lower() == "chunked":
        body = _decode_chunked_body(body)

    request = httpx.Request("POST", f"https://{host}/api/v1/chat/completions")
    response = httpx.Response(
        status_code=int(status_code_text),
        headers=headers,
        content=body,
        request=request,
    )
    response.raise_for_status()
    return response


def _decode_chunked_body(body: bytes) -> bytes:
    decoded = bytearray()
    view = memoryview(body)
    index = 0

    while index < len(view):
        line_end = body.find(b"\r\n", index)
        if line_end == -1:
            raise OpenRouterError("OpenRouter request failed")

        chunk_size = int(body[index:line_end].decode("ascii"), 16)
        index = line_end + 2
        if chunk_size == 0:
            break

        decoded.extend(view[index:index + chunk_size])
        index += chunk_size + 2

    return bytes(decoded)
