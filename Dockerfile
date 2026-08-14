FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
RUN useradd --create-home --uid 10001 lemono && mkdir -p /data && chown lemono:lemono /data
USER lemono
ENV LEMONO_DATA_DIR=/data
EXPOSE 8000
CMD ["uvicorn", "lemono.api:app", "--host", "0.0.0.0", "--port", "8000"]

