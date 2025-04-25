FROM python:3.11-slim-bookworm

WORKDIR /app

RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-root --without dev

COPY ./src_nhien /app/

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]