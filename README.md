# vivliostyle-pdf-page-generator

API HTTP que converte arquivos HTML/CSS/imagens em PDF usando o [Vivliostyle CLI](https://vivliostyle.org/), com FastAPI + uvicorn como servidor.

## Como funciona

1. O cliente envia um `multipart/form-data` onde **o nome de cada campo é o caminho relativo do arquivo** no projeto (ex.: `src/cover.html`, `styles/theme.css`).
2. A API monta um workspace temporário, gera (ou reutiliza) um `vivliostyle.config.js` e invoca o Vivliostyle CLI.
3. O PDF resultante é devolvido como `application/pdf`.

## Endpoints

| Método | Caminho        | Descrição                                      |
|--------|---------------|------------------------------------------------|
| POST   | `/render`     | Renderiza PDF a partir dos arquivos enviados   |
| POST   | `/render/demo`| Renderiza um PDF de exemplo (sem upload)       |
| GET    | `/health`     | Health check                                   |
| GET    | `/docs`       | Swagger UI (documentação interativa)           |

### Exemplo com `curl`

```bash
curl -X POST http://localhost:8000/render \
  -F "src/cover.html=@cover.html" \
  -F "styles/theme.css=@theme.css" \
  --output document.pdf
```

### `vivliostyle.config.js` personalizado

Envie o arquivo com o campo `vivliostyle.config.js` e ele será usado sem modificações:

```bash
curl -X POST http://localhost:8000/render \
  -F "vivliostyle.config.js=@vivliostyle.config.js" \
  -F "src/index.html=@index.html" \
  --output document.pdf
```

## Executando com Docker

```bash
# Build
docker build -t pdf-generator-api .

# Servidor (porta 8000)
docker run -p 8000:8000 pdf-generator-api

# Testes
docker run --rm -e APP_MODE=test pdf-generator-api
```

## Variáveis de ambiente

| Variável         | Padrão | Descrição                                              |
|-----------------|--------|--------------------------------------------------------|
| `APP_MODE`      | `serve`| `serve` inicia o servidor; `test` executa o pytest    |
| `VIVLIO_TIMEOUT`| `120`  | Tempo máximo (segundos) para o Vivliostyle gerar o PDF |

## Limites

- Tamanho máximo de requisição: **100 MB** (verificado tanto pelo `Content-Length` quanto para uploads chunked).
- Até 500 arquivos por requisição.

## Estrutura do projeto

```
app/
  main.py                   # FastAPI app, middleware de tamanho, handler de erros
  presentation/routes.py    # Endpoints /render e /render/demo
  application/service.py    # Orquestração: workspace → config → CLI → PDF
  infrastructure/
    vivlio.py               # Geração de config, chamada do CLI, projeto demo
    workdir.py              # Workspace temporário com sanitização de caminhos
tests/                      # pytest + pytest-asyncio
```
