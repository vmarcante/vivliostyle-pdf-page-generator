from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from app.presentation.routes import router

_MAX_REQUEST_SIZE = 100 * 1024 * 1024  # 100 MB


class LimitUploadSizeMiddleware:
    """Rejeita requisições com corpo maior que *max_bytes*.

    Cobre tanto uploads com ``Content-Length`` explícito quanto
    transferências ``chunked`` (sem esse cabeçalho).

    Funcionamento para chunked:

    1. O receive wrapper conta os bytes recebidos e, ao ultrapassar o
       limite, sinaliza fim de stream (``more_body=False``) para que o
       parser multipart pare de consumir dados.
    2. O send wrapper intercepta o início da resposta e a substitui por
       413 antes que qualquer byte seja enviado ao cliente.
    """

    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Verificação rápida quando o cabeçalho Content-Length está presente
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                if int(value) > self.max_bytes:
                    await self._send_413(send)
                    return
                break

        total = 0
        exceeded = False

        async def limited_receive():
            nonlocal total, exceeded
            msg = await receive()
            if msg.get("type") == "http.request":
                total += len(msg.get("body", b""))
                if total > self.max_bytes:
                    exceeded = True
                    # Encerra o stream para interromper o parser multipart
                    return {"type": "http.request", "body": b"", "more_body": False}
            return msg

        async def checked_send(message):
            # Se o limite foi ultrapassado, substitui qualquer resposta por 413
            if exceeded:
                if message.get("type") == "http.response.start":
                    await self._send_413(send)
                # Descarta demais mensagens (body chunks da resposta original)
                return
            await send(message)

        await self.app(scope, limited_receive, checked_send)

    async def _send_413(self, send) -> None:
        mb = self.max_bytes // (1024 * 1024)
        body = f"Requisição excede o limite de {mb} MB".encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"text/plain; charset=utf-8"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({"type": "http.response.body", "body": body})


app = FastAPI(
    title="Geração de PDF API",
    version="1.0.0",
    description=(
        "Recebe arquivos HTML/CSS/Imagens via multipart/form-data e gera um PDF com Vivliostyle.\n\n"
        "- Envie cada arquivo com o nome do campo como o caminho relativo desejado (ex.: `src/cover.html`, `styles/theme.css`).\n"
        "- Se `vivliostyle.config.js` for enviado, ele será utilizado. Caso contrário, um será gerado automaticamente."
    ),
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(LimitUploadSizeMiddleware, max_bytes=_MAX_REQUEST_SIZE)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> Response:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


app.include_router(router)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
