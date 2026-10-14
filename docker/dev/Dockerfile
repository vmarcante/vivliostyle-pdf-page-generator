FROM mcr.microsoft.com/playwright:v1.55.0-jammy

USER root

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONPATH=/app \
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

# Instala dependências de desenvolvimento (inclui ferramentas de teste)
COPY requirements-dev.txt /app/requirements-dev.txt
RUN pip3 install --no-cache-dir -r /app/requirements-dev.txt

# O código-fonte NÃO é copiado aqui.
# Ele é injetado como volume pelo docker-compose.yml,
# permitindo hot-reload sem reconstruir a imagem.

EXPOSE 8000

USER 1001

CMD ["python3", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--log-config", "logging.ini", "--reload"]
