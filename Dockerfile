# Dockerfile raiz — mantido para uso em CI e pipelines que executam
# `docker build .` na raiz do repositório.
#
# Para uso local com ambientes dedicados, prefira:
#   docker/dev/   → desenvolvimento (hot-reload, volume mounts)
#   docker/prod/  → produção (imagem enxuta, health check)

FROM mcr.microsoft.com/playwright:v1.55.0-jammy

USER root

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV APP_MODE=serve \
    PYTHONPATH=/app \
    HOME=/tmp \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    XDG_CONFIG_HOME=/tmp/.config \
    XDG_CACHE_HOME=/tmp/.cache \
    XDG_DATA_HOME=/tmp/.local/share \
    XDG_RUNTIME_DIR=/tmp/runtime

RUN mkdir -p /app \
    /tmp/.config \
    /tmp/.cache \
    /tmp/.local/share \
    /tmp/runtime \
    /ms-playwright \
 && chgrp -R 0 /app /tmp /ms-playwright \
 && chmod -R g=u /app /tmp /ms-playwright

RUN npm i -g @vivliostyle/cli@9.7.2

# Instala dependências completas (produção + teste) para suportar APP_MODE=test
COPY requirements-dev.txt /app/requirements-dev.txt
RUN pip3 install --no-cache-dir -r /app/requirements-dev.txt

COPY . /app
RUN chgrp -R 0 /app && chmod -R g=u /app

EXPOSE 8000

USER 1001

CMD ["sh", "-c", "if [ \"$APP_MODE\" = \"test\" ]; then python3 -m pytest -vv --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml; else python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-config logging.ini --timeout-keep-alive 30; fi"]
