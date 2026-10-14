from typing import List, Tuple

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from starlette.datastructures import UploadFile

from app.application.service import RenderService

router = APIRouter(tags=["render"])
service = RenderService()


@router.post(
    "/render",
    summary="Renderiza PDF",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "additionalProperties": {"type": "string", "format": "binary"},
                        "description": "Envie arquivos; o NOME DO CAMPO deve ser o caminho relativo (ex.: src/cover.html, styles/theme.css).",
                    }
                }
            },
        },
        "responses": {
            "200": {"description": "PDF gerado", "content": {"application/pdf": {}}}
        },
    },
)
async def render(request: Request) -> Response:
    form = await request.form(max_files=500, max_fields=500)
    items: List[Tuple[str, bytes]] = []
    for key, value in form.multi_items():
        if not isinstance(value, UploadFile):
            continue
        data = await value.read()
        if not data:
            continue
        items.append((str(key), data))

    if not items:
        raise HTTPException(
            status_code=400,
            detail=(
                "Envie arquivos como multipart; "
                "o nome do campo deve ser o caminho relativo (ex.: src/cover.html)"
            ),
        )

    pdf_bytes = await service.render_from_items(items)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=document.pdf"},
    )


@router.post("/render/demo", summary="Renderiza PDF de demonstração")
async def render_demo() -> Response:
    pdf_bytes = await service.render_demo()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=demo.pdf"},
    )
