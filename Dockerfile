FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SIGAE_ENV=production \
    SIGAE_DATABASE=/app/instance/sigae.db \
    SIGAE_AUTH_REQUIRED=true

WORKDIR /app

RUN addgroup --system sigae && adduser --system --ingroup sigae sigae

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt

COPY main.py arvore_avl.py arvore_rubro_negra.py heap_medicos.py heap_pacientes.py tabela_hash.py ./
COPY sigae ./sigae
COPY templates ./templates
COPY static ./static

RUN mkdir -p /app/instance && chown -R sigae:sigae /app
USER sigae

EXPOSE 5000
VOLUME ["/app/instance"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/v1/health', timeout=3)"

CMD ["python", "-m", "sigae.cli", "--host", "0.0.0.0", "--port", "5000"]
